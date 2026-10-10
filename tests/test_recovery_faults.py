from hashlib import sha256
from pathlib import Path

import pytest

from src.intent_revalidation.fixtures import mapping, sequence, string
from src.intent_revalidation.model import decode_json
from src.intent_revalidation.policies import Policy

from .recovery_support import Trace, array_records, records, run_trace


@pytest.fixture(scope="module")
def trace(tmp_path_factory: pytest.TempPathFactory) -> Trace:
    return run_trace(tmp_path_factory.mktemp("faults") / "study")


def test_fault_targets_archive_real_preimages_and_preserve_provenance(trace: Trace) -> None:
    # Given a completed trace with snapshots on both sides of each injected fault.
    for outcome in trace.outcomes:
        directory = trace.event(outcome)
        before = array_records(directory / "activation-cache.json")
        after = array_records(directory / "availability.json")
        journal = mapping(decode_json((directory / "fault.json").read_text()))
        before_by_id = {string(mapping(row["artifact"])["artifact_id"]): row for row in before}
        after_by_id = {string(mapping(row["artifact"])["artifact_id"]): row for row in after}
        targets = {target.artifact_id: target for target in outcome.fault.targets}
        # When the fault journal is matched to the actual bytes and immutable metadata.
        assert journal["event"] == outcome.event.event_id
        assert journal["workflow_executions"] == 0
        assert {string(mapping(row)["artifact_id"]) for row in sequence(journal["targets"])} == set(
            targets
        )
        assert before_by_id.keys() == after_by_id.keys()
        for identifier, original in before_by_id.items():
            damaged = after_by_id[identifier]
            metadata = mapping(original["artifact"])
            assert damaged["artifact"] == metadata
            if identifier not in targets:
                assert original == damaged
                continue
            target = targets[identifier]
            assert target.declared_sha256 == metadata["sha256"]
            assert target.pre_sha256 == original["actual_sha256"]
            assert target.post_sha256 == damaged["actual_sha256"]
            # Then existing preimages remain recoverable, and damage never repairs its hash.
            if original["present"] is True:
                assert target.archive_path is not None
                archive = Path(target.archive_path)
                assert sha256(archive.read_bytes()).hexdigest() == target.pre_sha256
                assert target.pre_sha256 == target.declared_sha256
            else:
                assert target.action == "already_missing"
                assert target.archive_path is None
            assert damaged["hash_valid"] is False
            assert damaged["actual_sha256"] != metadata["sha256"]
            if target.post_sha256 is None:
                assert not Path(target.path).exists()
            else:
                assert sha256(Path(target.path).read_bytes()).hexdigest() == target.post_sha256
        selected = {item.artifact_id for item in outcome.result.artifacts}
        assert not selected.intersection(targets)
        assert outcome.fault.duration_ns > 0


def test_fault_scope_and_history_fallback_follow_the_public_event_rules(trace: Trace) -> None:
    # Given the same fault rules applied to independent policy histories.
    target_steps = {"E2": "summary", "E3": "summary", "E4": "render", "E6": "select"}
    for outcome in trace.outcomes:
        event_id = outcome.event.event_id
        before = array_records(trace.event(outcome) / "activation-cache.json")
        # When eligible artifacts are reconstructed from step and requirement provenance.
        if event_id not in target_steps:
            assert outcome.fault.eligible_ids == ()
            assert outcome.fault.targets == ()
            continue
        candidates = [mapping(row["artifact"]) for row in before]
        eligible = [
            string(item["artifact_id"])
            for item in candidates
            if item["step"] == target_steps[event_id]
            and (
                event_id != "E4"
                or mapping(item["requirements"])["title"] == outcome.revision.requirements.title
            )
        ]
        # Then newest-only faults preserve fallback, and all-candidate faults exhaust the role.
        assert tuple(eligible) == outcome.fault.eligible_ids
        expected = eligible[-1:] if event_id in {"E2", "E6"} else eligible
        assert [target.artifact_id for target in outcome.fault.targets] == expected
        if event_id in {"E2", "E6"}:
            assert len(eligible) >= 2
        if outcome.policy != Policy.B0 and event_id == "E2":
            assert outcome.result.artifacts[1].generation_revision == "S0"
        if event_id == "E4":
            assert all(target.action == "corrupt" for target in outcome.fault.targets)
            assert outcome.result.artifacts[-1].generation_revision == "E4"


def test_selected_provenance_is_traceable_to_original_generation_record(trace: Trace) -> None:
    # Given separate generation records and point-in-time selection snapshots.
    for outcome in trace.outcomes:
        registry = records(trace.arm(outcome) / "artifacts.jsonl")
        originals = {string(row["artifact_id"]): row for row in registry}
        selected = array_records(trace.event(outcome) / "selected-artifacts/artifacts.json")
        # When selected metadata is compared to the original append-only generation ledger.
        assert len(selected) == 3
        for row in selected:
            original = originals[string(row["artifact_id"])]
            # Then cloning may relocate bytes but cannot rewrite generation or lineage fields.
            assert {key: value for key, value in row.items() if key != "path"} == {
                key: value for key, value in original.items() if key != "path"
            }
