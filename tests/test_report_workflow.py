from dataclasses import replace
from pathlib import Path
from typing import Final, Literal, assert_never

import pytest

from src.intent_revalidation.model import (
    InputError,
    Json,
    RevisionId,
    Validity,
    canonical,
    decode_json,
    digest,
)
from src.intent_revalidation.policies import Policy
from src.intent_revalidation.report_workflow.cache import check_artifact, run_revision
from src.intent_revalidation.report_workflow.evaluation import evaluate, source_oracle
from src.intent_revalidation.report_workflow.inputs import load_source, parse_source
from src.intent_revalidation.report_workflow.model import Column, ReportRequirements, Revision, Step
from src.intent_revalidation.report_workflow.operations import make_context
from src.intent_revalidation.report_workflow.reference import enumerate_plans
from src.intent_revalidation.report_workflow.storage import Request, Store

SOURCE: Final = Path(__file__).parents[1] / "runs/phase1-20261010-01/metrics.json"
INITIAL: Final = ReportRequirements(("D1", "D2", "D3", "D4", "D5"), "All cases", tuple(Column))


@pytest.mark.parametrize("policy", tuple(Policy))
def test_revision_stream_reuses_history_and_preserves_evidence(
    tmp_path: Path, policy: Policy
) -> None:
    original_source = SOURCE.read_bytes()
    context = make_context(load_source(SOURCE))
    seed = Store(tmp_path / "seed", context)
    initial = run_revision(seed, Policy.B0, Revision(RevisionId("r0"), INITIAL))
    seed_bytes = {item.path: item.path.read_bytes() for item in seed.cache}
    store = seed.clone(tmp_path / policy.value)
    renamed = replace(INITIAL, title="Observed comparison")
    reordered = replace(renamed, columns=tuple(reversed(INITIAL.columns)))
    changes = (renamed, reordered, replace(reordered, case_ids=("D4", "D5")), INITIAL)
    observed: list[int] = []
    references: list[int] = []
    for index, target in enumerate(changes, 1):
        before = store.cache
        result = run_revision(store, policy, Revision(RevisionId(f"r{index}"), target))
        references.append(enumerate_plans(before, target, context).minimum_executions)
        observed.append(result.counts.get("executions", 0))
        assert result.started_ns <= result.finished_ns
        assert result.counts["bind"] == len(Step)
        assert result.counts["publish"] == 1
        assert all(
            evaluate(item, target, context).validity == Validity.VALID for item in result.artifacts
        )
        if index < 3 and policy != Policy.B0:
            assert [item.sha256 for item in result.artifacts[:2]] == [
                item.sha256 for item in initial.artifacts[:2]
            ]
        if index == 4 and policy != Policy.B0:
            assert tuple(item.generation_revision for item in result.artifacts) == ("r0",) * 3
    assert observed == ([3, 3, 3, 3] if policy == Policy.B0 else [1, 1, 3, 0])
    assert references == [1, 1, 3, 0]
    assert SOURCE.read_bytes() == original_source
    assert {path: path.read_bytes() for path in seed_bytes} == seed_bytes
    assert all(item.generation_revision == "r0" for item in seed.cache)


@pytest.mark.parametrize("field", ["source_hash", "code_hash", "env_hash", "contract_version"])
def test_provenance_changes_reject_equal_content(tmp_path: Path, field: str) -> None:
    context = make_context(load_source(SOURCE))
    store = Store(tmp_path, context)
    result = run_revision(store, Policy.B0, Revision(RevisionId("r0"), INITIAL))
    artifact = replace(result.artifacts[-1], **{field: "changed"})
    assert evaluate(artifact, INITIAL, context).validity == Validity.INVALID
    assert (
        check_artifact(
            artifact,
            Request(Step.RENDER, Revision(RevisionId("r1"), INITIAL), result.artifacts[-2]),
            store,
        ).validity
        == Validity.INVALID
    )


def test_missing_provenance_is_unknown_and_forces_execution(tmp_path: Path) -> None:
    context = make_context(load_source(SOURCE))
    store = Store(tmp_path, context)
    initial = run_revision(store, Policy.B0, Revision(RevisionId("r0"), INITIAL))
    missing = replace(initial.artifacts[-1], generation_revision=RevisionId(""))
    store.artifacts[-1] = missing
    assert evaluate(missing, INITIAL, context).validity == Validity.UNKNOWN
    result = run_revision(store, Policy.B2, Revision(RevisionId("r1"), INITIAL))
    assert result.counts["executions"] == 1
    assert result.artifacts[-1].generation_revision == "r1"


def test_equal_totals_with_different_case_context_are_rejected(tmp_path: Path) -> None:
    context = make_context(load_source(SOURCE))
    target = replace(INITIAL, case_ids=("D1",))
    result = run_revision(Store(tmp_path, context), Policy.B0, Revision(RevisionId("r0"), target))
    other = replace(target, case_ids=("D5",))
    assert all(
        evaluate(item, other, context).validity == Validity.INVALID for item in result.artifacts
    )


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("5/5", "5/15"),
        ("B1 | 5/5 | 5", "B1 | 5/5 | 6"),
        ("Cases: D1, D2, D3, D4, D5", "Cases: D4, D5"),
    ],
)
def test_evaluator_rejects_semantic_corruption_with_matching_digest(
    tmp_path: Path,
    before: str,
    after: str,
) -> None:
    context = make_context(load_source(SOURCE))
    result = run_revision(Store(tmp_path, context), Policy.B0, Revision(RevisionId("r0"), INITIAL))
    report = result.artifacts[-1]
    content = report.path.read_bytes()
    modified = content.replace(before.encode(), after.encode())
    assert modified != content
    path = tmp_path / "corrupt.md"
    _ = path.write_bytes(modified)
    altered = replace(report, path=path, sha256=digest(modified))
    assert evaluate(altered, INITIAL, context).validity == Validity.INVALID


def test_evaluator_detects_input_dependent_production_parser_fault(tmp_path: Path) -> None:
    source = load_source(SOURCE)
    rows = tuple(
        replace(row, executions=row.executions + 9)
        if row.case_id == "D4" and row.policy == Policy.B1
        else row
        for row in source.rows
    )
    context = make_context(replace(source, rows=rows))
    target = replace(INITIAL, case_ids=("D4", "D5"))
    result = run_revision(Store(tmp_path, context), Policy.B0, Revision(RevisionId("r0"), target))
    assert all(
        evaluate(item, target, context).validity == Validity.INVALID for item in result.artifacts
    )


@pytest.mark.parametrize("mutation", ["boolean_count", "duplicate", "unbalanced"])
def test_malformed_observed_metrics_fail_at_input(
    mutation: Literal["boolean_count", "duplicate", "unbalanced"],
) -> None:
    value = decode_json(SOURCE.read_text())
    assert isinstance(value, list)
    modified: list[Json] = value.copy()
    match mutation:
        case "boolean_count":
            assert isinstance(modified[0], dict)
            counts = modified[0]["operation_counts"]
            assert isinstance(counts, dict)
            counts["policy_executions"] = True
        case "duplicate":
            modified.append(modified[0])
        case "unbalanced":
            _ = modified.pop()
        case unreachable:
            assert_never(unreachable)
    with pytest.raises(InputError):
        _ = parse_source(canonical(modified))
    content = canonical(modified)
    bad_source = replace(load_source(SOURCE), content=content, sha256=digest(content))
    with pytest.raises(InputError):
        _ = source_oracle(INITIAL, make_context(bad_source))


@pytest.mark.parametrize("change", ["source", "environment", "renderer", "shared"])
@pytest.mark.parametrize("policy", [Policy.B1, Policy.B2])
def test_actual_dependency_changes_invalidate_the_relevant_cache(
    tmp_path: Path,
    policy: Policy,
    change: Literal["source", "environment", "renderer", "shared"],
) -> None:
    source = load_source(SOURCE)
    context = make_context(source)
    store = Store(tmp_path, context)
    initial = run_revision(store, Policy.B0, Revision(RevisionId("r0"), INITIAL))
    expected = 3
    match change:
        case "source":
            changed = replace(context, source=parse_source(source.content + b"\n"))
        case "environment":
            changed = replace(context, env_hash=digest(b"new environment"))
        case "renderer":
            changed = replace(
                context, fingerprints=(*context.fingerprints[:2], digest(b"new render"))
            )
            expected = 1
        case "shared":
            changed = replace(
                context,
                fingerprints=tuple(
                    digest(item.encode() + b"change") for item in context.fingerprints
                ),
            )
        case unreachable:
            assert_never(unreachable)
    store.context = changed
    result = run_revision(store, policy, Revision(RevisionId("r1"), INITIAL))
    assert result.counts["executions"] == expected
    assert all(
        evaluate(item, INITIAL, changed).validity == Validity.VALID for item in result.artifacts
    )
    assert evaluate(initial.artifacts[-1], INITIAL, changed).validity == Validity.INVALID
    assert enumerate_plans(initial.artifacts, INITIAL, changed).minimum_executions == expected


def test_stage_fingerprints_cover_the_shared_model_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = load_source(SOURCE)
    original = make_context(source)
    read_bytes = Path.read_bytes

    def modified_read(path: Path) -> bytes:
        content = read_bytes(path)
        if path.name == "model.py" and path.parent.name == "report_workflow":
            return content + b"\n# dependency changed\n"
        return content

    monkeypatch.setattr(Path, "read_bytes", modified_read)
    changed = make_context(source)
    assert all(
        before != after
        for before, after in zip(original.fingerprints, changed.fingerprints, strict=True)
    )
