from collections import Counter
from hashlib import sha256
from pathlib import Path

import pytest

from src.intent_revalidation.fixtures import mapping, sequence, string
from src.intent_revalidation.model import ArtifactId, decode_json
from src.intent_revalidation.policies import Policy
from src.intent_revalidation.report_workflow.inputs import count

from .recovery_support import Trace, array_records, records, run_trace


@pytest.fixture(scope="module")
def trace(tmp_path_factory: pytest.TempPathFactory) -> Trace:
    return run_trace(tmp_path_factory.mktemp("recovery") / "study")


def test_executions_match_real_attempts_and_finite_reference(trace: Trace) -> None:
    # Given the public trace executed in three rotating policy orders.
    expected = {"E1": 1, "E2": 0, "E3": 1, "E4": 1, "E5": 0, "E6": 0}
    assert len(trace.outcomes) == 54
    # When actual starts/completions are counted independently of the reported costs.
    for outcome in trace.outcomes:
        attempts = records(trace.arm(outcome) / "attempts.jsonl")
        persisted = mapping(decode_json((trace.event(outcome) / "outcome.json").read_text()))
        relevant = tuple(
            row for row in attempts if mapping(row["attempt"])["revision"] == outcome.event.event_id
        )
        starts = {
            string(mapping(row["attempt"])["attempt_id"])
            for row in relevant
            if row["action"] == "start"
        }
        completions = {
            string(mapping(row["attempt"])["attempt_id"])
            for row in relevant
            if row["action"] == "complete"
        }
        executed = 3 if outcome.policy == Policy.B0 else expected[outcome.event.event_id]
        # Then no hidden fallback, missing attempt, or accounting-only execution can pass.
        assert len(relevant) == executed * 2
        assert len(starts) == executed
        assert starts == completions
        assert outcome.result.counts.get("executions", 0) == executed
        assert mapping(persisted["operation_counts"]).get("executions", 0) == len(starts)
        assert outcome.reference.minimum_executions == expected[outcome.event.event_id]
        assert (
            mapping(persisted["reference"])["minimum_executions"]
            == expected[outcome.event.event_id]
        )
        assert outcome.result.started_ns <= outcome.result.finished_ns
    for repeat in range(1, 4):
        for policy in Policy:
            selected = [
                item for item in trace.outcomes if item.repeat == repeat and item.policy == policy
            ]
            assert sum(item.result.counts.get("executions", 0) for item in selected) == (
                18 if policy == Policy.B0 else 3
            )
        ordered = [
            item.policy.value
            for item in trace.outcomes
            if item.repeat == repeat and item.event.event_id == "E1"
        ]
        assert ordered == ["B0", "B1", "B2"][repeat - 1 :] + ["B0", "B1", "B2"][: repeat - 1]


def test_each_report_matches_raw_phase1_bytes_without_production_oracle(trace: Trace) -> None:
    # Given preserved raw Phase 1 observations, independently grouped by their policy.
    source_rows = [mapping(value) for value in sequence(decode_json(trace.source.decode()))]
    source_hash = sha256(trace.source).hexdigest()
    assert (trace.root / "source_metrics.json").read_bytes() == trace.source
    # When every event's immutable selected report snapshot is parsed as a Markdown table.
    for outcome in trace.outcomes:
        requirements = outcome.revision.requirements
        report = (
            trace.event(outcome) / "selected-artifacts" / outcome.result.artifacts[-1].path.name
        )
        lines = report.read_text().splitlines()
        table = [
            [cell.strip() for cell in line.strip("|").split("|")]
            for line in lines
            if line.startswith("|")
        ]
        assert table[0] == list(requirements.columns)
        observed = {row[0]: row[1:] for row in table[2:]}
        # Then content, selection, title and provenance agree with the raw measurements.
        assert lines[0] == f"# {requirements.title}"
        assert f"Source SHA256: {source_hash}" in lines
        assert "Cases: " + ", ".join(requirements.case_ids) in lines
        assert len(table[2:]) == 3
        for policy in ("B0", "B1", "B2"):
            rows = [
                row
                for row in source_rows
                if row["policy"] == policy and row["case_id"] in requirements.case_ids
            ]
            valid = sum(mapping(row["audit"])["final_satisfied"] is True for row in rows)
            executions = sum(
                count(mapping(row["operation_counts"]).get("policy_executions", 0)) for row in rows
            )
            invalid = sum(count(mapping(row["audit"])["invalid_reuse_events"]) for row in rows)
            assert observed[policy] == [f"{valid}/{len(rows)}", str(executions), str(invalid)]
        for artifact in outcome.result.artifacts:
            snapshot = trace.event(outcome) / "selected-artifacts" / artifact.path.name
            assert sha256(snapshot.read_bytes()).hexdigest() == artifact.sha256
            assert artifact.source_hash == source_hash
            assert artifact.generation_revision
            assert artifact.code_hash
            assert artifact.env_hash
            assert artifact.contract_version


def test_seed_is_two_actual_duplicate_runs_and_every_clone_is_fair(trace: Trace) -> None:
    # Given the common seed generated by two real B0 runs with separate revision identities.
    seed = array_records(trace.root / "repeat-1/B0/initial-cache.json")
    artifacts = [mapping(row["artifact"]) for row in seed]
    attempts = records(trace.root / "seed/attempts.jsonl")
    # When actual seed attempts and the initial nine clone snapshots are examined.
    completions = [row for row in attempts if row["action"] == "complete"]
    assert Counter(string(mapping(row["attempt"])["revision"]) for row in completions) == {
        "S0": 3,
        "S1": 3,
    }
    assert len({string(mapping(row["attempt"])["attempt_id"]) for row in completions}) == 6
    assert len(artifacts) == 6
    for earlier, later in zip(artifacts[:3], artifacts[3:], strict=True):
        assert earlier["sha256"] == later["sha256"]
        assert earlier["artifact_id"] != later["artifact_id"]
        assert (earlier["generation_revision"], later["generation_revision"]) == ("S0", "S1")
    expected = [{key: value for key, value in row.items() if key != "path"} for row in artifacts]
    # Then policies receive equal bytes and metadata, without fabricating duplicate history.
    for repeat in range(1, 4):
        for policy in Policy:
            rows = array_records(
                trace.root / f"repeat-{repeat}" / policy.value / "initial-cache.json"
            )
            assert all(row["present"] is True and row["hash_valid"] is True for row in rows)
            metadata = [mapping(row["artifact"]) for row in rows]
            assert [
                {key: value for key, value in row.items() if key != "path"} for row in metadata
            ] == expected
    for artifact in artifacts:
        path = trace.root / "seed/artifacts" / Path(string(artifact["path"])).name
        assert sha256(path.read_bytes()).hexdigest() == artifact["sha256"]


def test_exposure_ledgers_keep_generation_revision_and_current_lineage(trace: Trace) -> None:
    # Given event snapshots preserve selected provenance before later damage.
    for outcome in trace.outcomes:
        rows = records(trace.arm(outcome) / "events.jsonl")
        # When every actual bind, consume and publication is read from the event ledger.
        exposures = [row for row in rows if row["revision"] == outcome.event.event_id]
        metadata = {item.artifact_id: item for item in outcome.result.artifacts}
        cached = 0
        assert Counter(string(row["action"]) for row in exposures) == {
            "bind": 3,
            "consume": 2,
            "publish": 1,
        }
        for row in exposures:
            artifact = metadata[ArtifactId(string(row["artifact_id"]))]
            expected = artifact.generation_revision != outcome.revision.revision_id
            assert row["cached"] == expected
            cached += int(expected)
        # Then actual exposure counts and lineage, rather than inspections, justify the audit.
        assert outcome.audit.final_satisfied
        assert outcome.audit.actual_use_events == len(exposures) == 6
        assert outcome.audit.cache_use_events == cached
        assert outcome.audit.invalid_use_events == outcome.audit.invalid_reuse_events == 0
        assert outcome.audit.lineage_violations == 0
        if outcome.policy != Policy.B0 and outcome.event.event_id == "E3":
            assert [item.generation_revision for item in outcome.result.artifacts] == [
                "S1",
                "E3",
                "E1",
            ]
        if outcome.policy != Policy.B0 and outcome.event.event_id == "E5":
            assert outcome.result.artifacts[-1].generation_revision == "S1"
        if outcome.policy != Policy.B0 and outcome.event.event_id == "E6":
            assert outcome.result.artifacts[0].generation_revision == "S0"
