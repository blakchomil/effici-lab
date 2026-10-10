"""Real persisted runs: each test separates fixture setup, action, and observations."""

from pathlib import Path
from typing import Final

import pytest

from src.intent_revalidation.evaluation import evaluate
from src.intent_revalidation.experiment import run_experiment
from src.intent_revalidation.fixtures import (
    load_suite,
    mapping,
    parse_requirements,
    sequence,
    string,
)
from src.intent_revalidation.model import (
    Artifact,
    ArtifactId,
    AttemptId,
    Context,
    InputError,
    Json,
    RevisionId,
    Task,
    Validity,
    canonical,
    decode_json,
)
from src.intent_revalidation.policies import Policy

CASES: Final = Path("examples/dev_cases.json")


def records(path: Path) -> tuple[dict[str, Json], ...]:
    return tuple(mapping(decode_json(line)) for line in path.read_text().splitlines())


def artifact_from_record(record: dict[str, Json]) -> Artifact:
    return Artifact(
        ArtifactId(string(record["id"])),
        Task(string(record["task_id"])),
        Path(string(record["path"])),
        string(record["sha256"]),
        AttemptId(string(record["attempt_id"])),
        RevisionId(string(record["revision_id"])),
        parse_requirements(record["requirements"]),
        tuple(ArtifactId(string(value)) for value in sequence(record["input_ids"])),
        tuple(string(value) for value in sequence(record["input_hashes"])),
        string(record["source_sha256"]),
        string(record["code_sha256"]),
        string(record["environment_sha256"]),
        string(record["contract_version"]),
        string(record["cache_key"]),
    )


def test_current_artifacts_satisfy_contracts_when_all_baselines_run(tmp_path: Path) -> None:
    suite = load_suite(CASES)
    root = tmp_path / "run"

    outcomes = run_experiment(CASES, root, "pytest integration")

    manifest = mapping(decode_json((root / "manifest.json").read_text()))
    context = Context(
        suite.dataset_id,
        (root / "source.csv").read_bytes(),
        string(manifest["source_sha256"]),
        string(manifest["code_sha256"]),
        string(manifest["environment_sha256"]),
        string(manifest["contract_version"]),
    )
    targets = {case.id: case.target.requirements for case in suite.cases}
    assert len(outcomes) == 15
    for outcome in outcomes:
        folder = root / outcome.case_id / outcome.policy.value
        current = mapping(decode_json((folder / "current.json").read_text()))
        artifacts = {
            item.id: item for item in map(artifact_from_record, records(folder / "artifacts.jsonl"))
        }
        selected = mapping(current["artifacts"])
        assert set(selected) == {task.value for task in Task}
        for identifier in selected.values():
            actual = artifacts[ArtifactId(string(identifier))]
            assert evaluate(actual, targets[outcome.case_id], context).validity is Validity.VALID
        assert outcome.audit.final_satisfied
        assert outcome.audit.invalid_reuse_events == 0


def test_costs_and_cache_fairness_when_baselines_share_initial_work(tmp_path: Path) -> None:
    root = tmp_path / "run"
    minimum = {"D1": 1, "D2": 2, "D3": 0, "D4": 1, "D5": 1}

    outcomes = run_experiment(CASES, root, "pytest cost accounting")

    seeds = [
        event
        for path in root.glob("*/initial/events.jsonl")
        for event in records(path)
        if event["type"] == "run_completed"
    ]
    assert len(seeds) == 17
    for case_id in minimum:
        fingerprints = [
            (root / case_id / policy.value / "activation_cache.json").read_bytes()
            for policy in Policy
        ]
        assert len(set(fingerprints)) == 1
    for outcome in outcomes:
        events = records(root / outcome.case_id / outcome.policy.value / "events.jsonl")
        for phase in ("initial", "late", "policy"):
            completed = [
                event
                for event in events
                if event["type"] == "run_completed" and event["phase"] == phase
            ]
            count = (
                outcome.initial_executions
                if phase == "initial"
                else outcome.counters.get(f"{phase}_executions", 0)
            )
            duration = (
                outcome.initial_compute_ns
                if phase == "initial"
                else outcome.durations_ns.get(f"{phase}_executions", 0)
            )
            assert count == len(completed)
            assert duration == sum(int(str(event["compute_ns"])) for event in completed)
        actual_count = outcome.counters.get("policy_executions", 0)
        assert outcome.reference.minimum_executions == minimum[outcome.case_id]
        assert actual_count == (4 if outcome.policy is Policy.B0 else minimum[outcome.case_id])
        assert outcome.counters.get("late_executions", 0) == int(outcome.case_id in {"D4", "D5"})
        assert outcome.unnecessary_executions == actual_count - minimum[outcome.case_id]


def test_late_completion_precedes_policy_and_preserves_revision_when_replayed(
    tmp_path: Path,
) -> None:
    root = tmp_path / "run"

    _ = run_experiment(CASES, root, "pytest replay ordering")

    for case_id in ("D4", "D5"):
        for policy in Policy:
            folder = root / case_id / policy.value
            events = records(folder / "events.jsonl")
            late_start = next(
                index
                for index, event in enumerate(events)
                if event["type"] == "run_started" and event["phase"] == "late"
            )
            changed = next(
                index
                for index, event in enumerate(events)
                if event["type"] == "requirements_changed"
            )
            late_end = next(
                index
                for index, event in enumerate(events)
                if event["type"] == "run_completed" and event["phase"] == "late"
            )
            activated = next(
                index for index, event in enumerate(events) if event["type"] == "policy_activated"
            )
            assert late_start < changed < late_end < activated
            assert (
                events[late_start]["revision_id"] == events[late_end]["started_revision_id"] == "r0"
            )
            assert [
                event["fixture_sequence"]
                for event in events[:activated]
                if event["type"] == "fixture_event"
            ] == [1, 2, 3]
            assert all(
                event["type"] not in {"artifact_assessed", "artifact_bound", "artifact_constructed"}
                and event.get("phase") != "policy"
                for event in events[changed:activated]
            )
            late_id = events[late_end]["artifact_id"]
            late = next(
                record for record in records(folder / "artifacts.jsonl") if record["id"] == late_id
            )
            assert late["revision_id"] == "r0"
            current = mapping(decode_json((folder / "current.json").read_text()))
            assert current["revision_id"] == "r1"
            assert Path(string(current["report_path"])).suffix == ".html"
            assert all(
                event["artifact_id"] != late_id
                for event in events
                if case_id == "D5"
                and event["type"] == "report_published"
                and event["revision_id"] == "r1"
            )


def test_existing_run_is_preserved_when_reexecution_is_requested(tmp_path: Path) -> None:
    root = tmp_path / "run"
    _ = run_experiment(CASES, root, "first invocation")
    before = {
        path.relative_to(root): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in root.rglob("*")
        if path.is_file()
    }

    with pytest.raises(FileExistsError):
        _ = run_experiment(CASES, root, "second invocation")

    assert {
        path.relative_to(root): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in root.rglob("*")
        if path.is_file()
    } == before


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("metric", {"operation": "average", "field": "amount_cents", "unit": "cents"}),
        ("period", {"start_inclusive": "2026-02-01", "end_exclusive": "2026-01-01"}),
        ("period", {"start_inclusive": "2026-01-01", "end_exclusive": "2026-01-01"}),
        ("period", {"start_inclusive": "2026-02-30", "end_exclusive": "2026-03-01"}),
    ],
)
def test_invalid_semantics_are_rejected_before_writing(
    tmp_path: Path, field: str, value: Json
) -> None:
    fixture = mapping(decode_json(CASES.read_text()))
    target = mapping(mapping(sequence(fixture["cases"])[0])["target_revision"])
    mapping(target["requirements"])[field] = value
    cases = tmp_path / "cases.json"
    _ = cases.write_bytes(canonical(fixture))
    _ = (tmp_path / "usage.csv").write_bytes(Path("examples/usage.csv").read_bytes())
    root = tmp_path / "run"

    with pytest.raises(InputError) as error:
        _ = run_experiment(cases, root, "invalid input")

    assert error.value.field == field
    assert not root.exists()
