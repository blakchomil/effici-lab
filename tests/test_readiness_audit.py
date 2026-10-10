from pathlib import Path
from typing import Final

import pytest

from src.intent_revalidation.fixtures import mapping
from src.intent_revalidation.model import RevisionId, canonical, decode_json, digest
from src.intent_revalidation.policies import Policy
from src.intent_revalidation.readiness_workflow.audit import audit_arm
from src.intent_revalidation.readiness_workflow.execution import Arm, CaseInputs, execute_arm
from src.intent_revalidation.readiness_workflow.inputs import parse_clarification, parse_snapshot
from src.intent_revalidation.readiness_workflow.model import Control
from src.intent_revalidation.report_workflow.cache import run_revision
from src.intent_revalidation.report_workflow.inputs import load_source
from src.intent_revalidation.report_workflow.model import Column, ReportRequirements, Revision
from src.intent_revalidation.report_workflow.operations import make_context
from src.intent_revalidation.report_workflow.storage import Store

ROOT: Final = Path(__file__).parents[1]


@pytest.fixture
def seeded(tmp_path: Path) -> tuple[Store, CaseInputs]:
    requirements = ReportRequirements(
        ("D1", "D2", "D3", "D4", "D5"), "Preserved results", tuple(Column)
    )
    source = load_source(ROOT / "runs/phase1-20261010-01/metrics.json")
    seed = Store(tmp_path / "seed", make_context(source))
    initial = run_revision(seed, Policy.B0, Revision(RevisionId("seed-R0"), requirements))
    example = ROOT / "examples/support-readiness"
    inputs = CaseInputs(
        parse_snapshot((example / "current-facts-20261010.json").read_bytes()),
        parse_clarification((example / "clarification-20261010.json").read_bytes()),
        requirements,
        (example / "request.md").read_bytes(),
        initial.artifacts[-1].path.read_bytes(),
    )
    return seed.clone(tmp_path / "arm"), inputs


def test_valid_b1_runtime_counts_actual_cached_exposures(seeded: tuple[Store, CaseInputs]) -> None:
    # Given a real cached numeric report, consumed by readiness composition.
    store, inputs = seeded
    run = execute_arm(store, Arm(Control.RULE, Policy.B1), inputs)
    # When all actual numeric and composition exposures are audited.
    result = mapping(audit_arm(run, inputs))
    # Then three bindings, two intermediate consumes, and both report uses are counted.
    assert result["final_satisfied"] is True
    assert result["cache_exposure_events"] == 7
    assert result["invalid_reuse_events"] == 0
    assert result["numeric_stage_executions"] == 0
    assert result["numeric_stage_reuses"] == 3
    assert result["composition_executions"] == 1


def test_corrupt_cached_numeric_bytes_fail_despite_valid_final_document(
    seeded: tuple[Store, CaseInputs],
) -> None:
    # Given an intact published composition but a corrupted cached numeric artifact.
    store, inputs = seeded
    run = execute_arm(store, Arm(Control.RULE, Policy.B1), inputs)
    report = run.numeric.artifacts[-1]
    _ = report.path.write_bytes(report.path.read_bytes() + b"unsupported claim\n")
    # When the auditor examines the actual source artifact and its exposures.
    result = mapping(audit_arm(run, inputs))
    # Then its binding, numeric publication, and composition consumption are invalid reuse.
    assert mapping(result["document_check"])["validity"] == "valid"
    assert result["final_satisfied"] is False
    assert result["invalid_reuse_events"] == 3


def test_extra_invalid_cached_consumption_is_counted_despite_valid_final_document(
    seeded: tuple[Store, CaseInputs],
) -> None:
    # Given an additional actual cached consumption with bytes unlike the recorded artifact.
    store, inputs = seeded
    run = execute_arm(store, Arm(Control.RULE, Policy.B1), inputs)
    report = run.numeric.artifacts[-1]
    store.record(
        "readiness-events.jsonl",
        {
            "action": "consume",
            "role": "numeric_report",
            "artifact_id": report.artifact_id,
            "actual_sha256": digest(b"stale numeric content"),
            "expected_sha256": report.sha256,
            "cached": True,
        },
    )
    # When the auditor evaluates the entire observed history, including the extra use.
    result = mapping(audit_arm(run, inputs))
    # Then the bad cached exposure is counted even though the final output is correct.
    assert mapping(result["document_check"])["validity"] == "valid"
    assert result["final_satisfied"] is False
    assert result["cache_exposure_events"] == 8
    assert result["invalid_reuse_events"] == 1


def test_changed_publication_pointer_fails_lineage_despite_valid_document(
    seeded: tuple[Store, CaseInputs],
) -> None:
    # Given the published pointer redirects away from the valid composed document.
    store, inputs = seeded
    run = execute_arm(store, Arm(Control.RULE, Policy.B1), inputs)
    _ = (store.root / "current-readiness.json").write_bytes(
        canonical({"path": "stale-readiness.md", "sha256": digest(run.document.read_bytes())})
    )
    # When the auditor checks the actual publication binding.
    result = mapping(audit_arm(run, inputs))
    # Then lineage fails without inventing an invalid cache reuse event.
    assert mapping(result["document_check"])["validity"] == "valid"
    assert result["final_satisfied"] is False
    assert result["composition_lineage_violations"] == 1
    assert result["invalid_reuse_events"] == 0


@pytest.mark.parametrize("remove_file", [False, True])
def test_missing_composition_attempt_evidence_fails_audit(
    seeded: tuple[Store, CaseInputs], *, remove_file: bool
) -> None:
    # Given a valid runtime result with its composition attempt evidence absent.
    store, inputs = seeded
    run = execute_arm(store, Arm(Control.RULE, Policy.B1), inputs)
    attempts = store.root / "composition-attempts.jsonl"
    if remove_file:
        attempts.unlink()
    else:
        _ = attempts.write_bytes(b"")
    # When evidence is audited rather than inferred from the surviving report.
    result = mapping(audit_arm(run, inputs))
    # Then missing provenance fails closed and no starts are counted without evidence.
    assert mapping(result["document_check"])["validity"] == "valid"
    assert result["final_satisfied"] is False
    assert result["composition_executions"] == 0


@pytest.mark.parametrize(
    "field_name",
    [
        "attempt_id",
        "revision",
        "input_report_sha256",
        "facts_sha256",
        "output_sha256",
        "code_sha256",
        "environment_sha256",
    ],
)
def test_mismatched_composition_completion_provenance_fails_audit(
    seeded: tuple[Store, CaseInputs], field_name: str
) -> None:
    # Given a real completed attempt whose provenance disagrees with runtime evidence.
    store, inputs = seeded
    run = execute_arm(store, Arm(Control.RULE, Policy.B1), inputs)
    attempts = store.root / "composition-attempts.jsonl"
    records = [mapping(decode_json(line)) for line in attempts.read_text().splitlines()]
    records[-1][field_name] = "mismatched-provenance"
    _ = attempts.write_bytes(b"".join(canonical(record) for record in records))
    # When completion is audited against its actual start and dependencies.
    result = mapping(audit_arm(run, inputs))
    # Then correct final content cannot compensate for missing provenance validity.
    assert mapping(result["document_check"])["validity"] == "valid"
    assert result["final_satisfied"] is False


def test_composition_execution_count_includes_additional_recorded_start(
    seeded: tuple[Store, CaseInputs],
) -> None:
    # Given an additional composition start following a completed valid publication.
    store, inputs = seeded
    run = execute_arm(store, Arm(Control.RULE, Policy.B1), inputs)
    store.record(
        "composition-attempts.jsonl",
        {
            "action": "start",
            "attempt_id": "additional-attempt",
            "revision": run.revision.revision_id,
            "started_ns": run.numeric.finished_ns + run.composition_ns + 1,
        },
    )
    # When total work is measured from recorded execution evidence.
    result = mapping(audit_arm(run, inputs))
    # Then both started compositions count, and the incomplete attempt fails the audit.
    assert result["composition_executions"] == 2
    assert result["total_stage_executions"] == 2
    assert result["final_satisfied"] is False


def test_semantically_equal_numeric_block_must_preserve_original_bytes(
    seeded: tuple[Store, CaseInputs],
) -> None:
    # Given a whitespace-only numeric edit with consistent publication hashes.
    store, inputs = seeded
    run = execute_arm(store, Arm(Control.RULE, Policy.B1), inputs)
    changed_numeric = inputs.previous_report.replace(b"| B0 |", b"|  B0 |", 1)
    assert changed_numeric != inputs.previous_report
    changed = run.document.read_bytes().replace(inputs.previous_report, changed_numeric, 1)
    _ = run.document.write_bytes(changed)
    changed_hash = digest(changed)
    events_path = store.root / "readiness-events.jsonl"
    events = [mapping(decode_json(line)) for line in events_path.read_text().splitlines()]
    events[-1]["actual_sha256"] = changed_hash
    events[-1]["expected_sha256"] = changed_hash
    _ = events_path.write_bytes(b"".join(canonical(event) for event in events))
    _ = (store.root / "current-readiness.json").write_bytes(
        canonical({"path": run.document.name, "sha256": changed_hash})
    )
    attempts = store.root / "composition-attempts.jsonl"
    records = [mapping(decode_json(line)) for line in attempts.read_text().splitlines()]
    records[-1]["output_sha256"] = changed_hash
    _ = attempts.write_bytes(b"".join(canonical(record) for record in records))
    # When exact preservation is checked independently of semantic numerical correctness.
    result = mapping(audit_arm(run, inputs))
    # Then the semantic oracle passes while byte preservation and the final contract fail.
    assert mapping(result["document_check"])["validity"] == "valid"
    assert result["numeric_bytes_preserved"] is False
    assert result["final_satisfied"] is False
