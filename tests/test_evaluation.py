from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from src.intent_revalidation.evaluation import evaluate
from src.intent_revalidation.model import (
    TASKS,
    Artifact,
    ArtifactId,
    AttemptId,
    Context,
    Requirements,
    RevisionId,
    Task,
    Validity,
    digest,
)
from src.intent_revalidation.pipeline import execute
from src.intent_revalidation.reference import enumerate_plans


@dataclass(frozen=True, slots=True)
class Scenario:
    target: Requirements
    context: Context
    cache: tuple[Artifact, ...]


@pytest.fixture
def scenario(tmp_path: Path) -> Scenario:
    source = Path("examples/usage.csv").read_bytes()
    context = Context("synthetic_usage_v1", source, digest(source), "code-v1", "env-v1")
    target = Requirements(
        "synthetic_usage_v1", "2026-01-01", "2026-02-01", "markdown", "en", "Usage report"
    )
    cache: list[Artifact] = []
    for task in TASKS:
        inputs = tuple(cache[-1:])
        content = execute(task, target, context, inputs)
        path = tmp_path / task.value
        _ = path.write_bytes(content)
        cache.append(
            Artifact(
                ArtifactId(task.value),
                task,
                path,
                digest(content),
                AttemptId(task.value),
                RevisionId("r0"),
                target,
                tuple(item.id for item in inputs),
                tuple(item.sha256 for item in inputs),
                context.source_sha256,
                context.code_sha256,
                context.environment_sha256,
                context.contract_version,
                "test",
            )
        )
    return Scenario(target, context, tuple(cache))


def altered(artifact: Artifact, content: bytes) -> Artifact:
    path = artifact.path.with_suffix(".altered")
    _ = path.write_bytes(content)
    return replace(artifact, path=path, sha256=digest(content))


@pytest.mark.parametrize("task", TASKS)
def test_accepts_actual_stage_output_when_source_matches(scenario: Scenario, task: Task) -> None:
    # Given a real stage output produced from the complete source.
    artifact = scenario.cache[TASKS.index(task)]
    # When independently evaluated.
    result = evaluate(artifact, scenario.target, scenario.context)
    # Then its role content is valid.
    assert result.validity is Validity.VALID


@pytest.mark.parametrize("task", [Task.LOAD, Task.NORMALIZE])
def test_rejects_incomplete_snapshot_when_requested_month_is_still_covered(
    scenario: Scenario, task: Task
) -> None:
    # Given a snapshot missing a February record while the request remains January.
    artifact = scenario.cache[TASKS.index(task)]
    content = artifact.path.read_bytes()
    start = content.rfind(b"{", 0, content.index(b"2026-02-01"))
    end = content.index(b"},", start) + 2
    partial = altered(artifact, content[:start] + content[end:])
    # When the complete-snapshot contract is checked.
    result = evaluate(partial, scenario.target, scenario.context)
    # Then matching January context cannot conceal missing records.
    assert result.validity is Validity.INVALID


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (b"2026-01-01", b"2025-01-01"),
        (b'"cents"', b'"dollars"'),
        (b"synthetic_usage_v1", b"other_dataset"),
        (b'"category"', b'"region"'),
        (b'"sum"', b'"average"'),
    ],
)
def test_rejects_wrong_aggregate_semantics_when_totals_are_equal(
    scenario: Scenario, old: bytes, new: bytes
) -> None:
    # Given unchanged totals with one incorrect context field and a valid byte digest.
    artifact = scenario.cache[2]
    wrong = altered(artifact, artifact.path.read_bytes().replace(old, new))
    # When independently evaluated.
    result = evaluate(wrong, scenario.target, scenario.context)
    # Then equal totals do not establish semantic validity.
    assert result.validity is Validity.INVALID


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (b"4000", b"4001"),
        (b"Unit: cents", b"Unit: dollars"),
        (b"Period: [2026-01-01", b"Period: [2025-01-01"),
        (b"Dataset: synthetic_usage_v1", b"Dataset: another"),
        (b"Language: en", b"Language: fr"),
        (b"# Usage report", b"# Wrong title"),
    ],
)
def test_rejects_report_corruption_when_metadata_and_digest_are_consistent(
    scenario: Scenario, old: bytes, new: bytes
) -> None:
    # Given altered visible report content with freshly computed digest.
    artifact = scenario.cache[3]
    wrong = altered(artifact, artifact.path.read_bytes().replace(old, new))
    # When the actual report is parsed.
    result = evaluate(wrong, scenario.target, scenario.context)
    # Then provenance alone cannot approve the report.
    assert result.validity is Validity.INVALID


def test_rejects_wrong_format_when_totals_match(scenario: Scenario) -> None:
    # Given a Markdown report after a change to HTML.
    target = replace(scenario.target, output_format="html")
    # When evaluated for the new output contract.
    result = evaluate(scenario.cache[3], target, scenario.context)
    # Then it cannot be published as HTML.
    assert result.validity is Validity.INVALID


@pytest.mark.parametrize("hidden", [False, True])
def test_checks_html_visible_structure_when_report_is_rendered(
    scenario: Scenario, *, hidden: bool
) -> None:
    # Given a real HTML report, optionally hiding its otherwise correct table.
    target = replace(scenario.target, output_format="html")
    content = execute(Task.RENDER, target, scenario.context, (scenario.cache[2],))
    if hidden:
        content = content.replace(b"<table>", b'<table hidden="hidden">')
    artifact = altered(scenario.cache[3], content)
    # When the HTML structure and visible text are independently parsed.
    result = evaluate(artifact, target, scenario.context)
    # Then hidden content is rejected and visible content is accepted.
    assert result.validity is (Validity.INVALID if hidden else Validity.VALID)


@pytest.mark.parametrize(
    "field", ["source_sha256", "code_sha256", "environment_sha256", "contract_version"]
)
def test_rejects_stale_provenance_when_content_matches(scenario: Scenario, field: str) -> None:
    # Given correct bytes with an obsolete provenance fingerprint.
    artifact = replace(scenario.cache[3], **{field: "obsolete"})
    # When checked against current context.
    result = evaluate(artifact, scenario.target, scenario.context)
    # Then matching content cannot bypass the execution contract.
    assert result.validity is Validity.INVALID


def test_enumerates_all_feasible_plans_when_complete_cache_matches(scenario: Scenario) -> None:
    # Given one compatible artifact per stage and unit execution cost.
    # When every cached-or-fresh combination is enumerated.
    result = enumerate_plans(scenario.cache, scenario.target, scenario.context)
    # Then all sixteen combinations work, including the zero-execution plan.
    assert (result.enumerated_plans, result.valid_plans, result.minimum_executions) == (16, 16, 0)


def test_reference_requires_report_execution_when_cached_report_is_corrupt(
    scenario: Scenario,
) -> None:
    # Given a semantically wrong report with an internally consistent byte digest.
    report = altered(scenario.cache[3], scenario.cache[3].path.read_bytes().replace(b"4000", b"1"))
    cache = (*scenario.cache[:3], report)
    # When plans are exhaustively checked.
    result = enumerate_plans(cache, scenario.target, scenario.context)
    # Then every cached-report plan is rejected and a fresh report is necessary.
    assert (result.enumerated_plans, result.valid_plans, result.minimum_executions) == (16, 8, 1)
    assert result.minimum_actions[-1] == "execute:render"


def test_reference_rejects_incompatible_input_hash_when_bytes_are_correct(
    scenario: Scenario,
) -> None:
    # Given a correct aggregate claiming an unavailable normalized input.
    aggregate = replace(scenario.cache[2], input_hashes=("unavailable",))
    cache = (*scenario.cache[:2], aggregate, scenario.cache[3])
    # When dependency-compatible plans are enumerated.
    result = enumerate_plans(cache, scenario.target, scenario.context)
    # Then all plans reusing this aggregate fail; executing it restores feasibility.
    assert (result.enumerated_plans, result.valid_plans, result.minimum_executions) == (16, 8, 1)
    assert result.minimum_actions[2] == "execute:aggregate"


def test_reference_cannot_use_future_cache_when_no_artifact_exists(scenario: Scenario) -> None:
    # Given no cache at the decision point.
    # When the finite plan space is enumerated.
    result = enumerate_plans((), scenario.target, scenario.context)
    # Then exactly one plan exists and all four executions are required.
    assert (result.enumerated_plans, result.valid_plans, result.minimum_executions) == (1, 1, 4)
