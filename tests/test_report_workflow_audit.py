from dataclasses import replace
from pathlib import Path
from typing import Final

from src.intent_revalidation.model import RevisionId, Validity
from src.intent_revalidation.policies import Policy
from src.intent_revalidation.report_workflow.audit import audit_revision
from src.intent_revalidation.report_workflow.cache import run_revision
from src.intent_revalidation.report_workflow.evaluation import evaluate
from src.intent_revalidation.report_workflow.inputs import load_source
from src.intent_revalidation.report_workflow.model import Column, ReportRequirements, Revision
from src.intent_revalidation.report_workflow.operations import make_context
from src.intent_revalidation.report_workflow.storage import Exposure, Store

SOURCE: Final = Path(__file__).parents[1] / "runs/phase1-20261010-01/metrics.json"
INITIAL: Final = ReportRequirements(("D1", "D2", "D3", "D4", "D5"), "All cases", tuple(Column))


def test_rejected_inspection_does_not_count_as_actual_use(tmp_path: Path) -> None:
    store = Store(tmp_path, make_context(load_source(SOURCE)))
    _ = run_revision(store, Policy.B0, Revision(RevisionId("r0"), INITIAL))
    revision = Revision(RevisionId("r1"), replace(INITIAL, title="Changed heading"))
    result = run_revision(store, Policy.B2, revision)
    audit = audit_revision(store, revision, result.artifacts)
    assert audit.final_satisfied
    assert audit.actual_use_events == 6
    assert audit.cache_use_events == 4
    assert audit.invalid_reuse_events == 0
    assert audit.invalid_use_events == 0
    assert result.counts["executions"] == 1
    assert result.counts["contract_checks"] == 3
    store.record(
        "assessments.jsonl",
        {
            "revision": revision.revision_id,
            "artifact_id": store.cache[0].artifact_id,
            "step": "select",
            "validity": "invalid",
            "reason": "injected rejected inspection",
        },
    )
    assert audit_revision(store, revision, result.artifacts) == audit


def test_stale_publication_after_success_then_restoration_is_audited(tmp_path: Path) -> None:
    store = Store(tmp_path, make_context(load_source(SOURCE)))
    initial = run_revision(store, Policy.B0, Revision(RevisionId("r0"), INITIAL))
    revision = Revision(RevisionId("r1"), replace(INITIAL, title="Changed heading"))
    result = run_revision(store, Policy.B2, revision)
    store.expose("publish", Exposure(revision, initial.artifacts[-1], cached=True))
    store.expose("publish", Exposure(revision, result.artifacts[-1], cached=False))
    audit = audit_revision(store, revision, result.artifacts)
    assert not audit.final_satisfied
    assert audit.publication_count == 3
    assert audit.actual_use_events == 8
    assert audit.cache_use_events == 5
    assert audit.invalid_reuse_events == 1
    assert audit.invalid_use_events == 1
    assert audit.lineage_violations == 1


def test_actual_binding_hash_must_match_consumed_predecessor(tmp_path: Path) -> None:
    store = Store(tmp_path, make_context(load_source(SOURCE)))
    revision = Revision(RevisionId("r0"), INITIAL)
    result = run_revision(store, Policy.B0, revision)
    wrong = replace(result.artifacts[1], input_hash="wrong-input")
    store.artifacts[1] = wrong
    selected = (result.artifacts[0], wrong, result.artifacts[2])
    audit = audit_revision(store, revision, selected)
    assert not audit.final_satisfied
    assert audit.invalid_use_events == 2
    assert audit.lineage_violations == 1
    assert evaluate(selected[-1], INITIAL, store.context).validity == Validity.VALID


def test_actual_consumption_must_use_currently_bound_artifact(tmp_path: Path) -> None:
    store = Store(tmp_path, make_context(load_source(SOURCE)))
    revision = Revision(RevisionId("r0"), INITIAL)
    result = run_revision(store, Policy.B0, revision)
    store.expose("consume", Exposure(revision, result.artifacts[0], cached=False))
    audit = audit_revision(store, revision, result.artifacts)
    assert not audit.final_satisfied
    assert audit.actual_use_events == 7
    assert audit.invalid_use_events == 0
    assert audit.lineage_violations == 1


def test_invalid_intermediate_exposure_fails_despite_valid_final_report(tmp_path: Path) -> None:
    store = Store(tmp_path, make_context(load_source(SOURCE)))
    revision = Revision(RevisionId("r0"), INITIAL)
    result = run_revision(store, Policy.B0, revision)
    wrong = replace(result.artifacts[0], code_hash="untrusted-code")
    store.artifacts[0] = wrong
    selected = (wrong, result.artifacts[1], result.artifacts[2])
    audit = audit_revision(store, revision, selected)
    assert evaluate(selected[-1], INITIAL, store.context).validity == Validity.VALID
    assert audit.invalid_use_events == 2
    assert audit.lineage_violations == 0
    assert not audit.final_satisfied


def test_cached_event_label_is_cross_checked_against_generation_revision(tmp_path: Path) -> None:
    store = Store(tmp_path, make_context(load_source(SOURCE)))
    revision = Revision(RevisionId("r0"), INITIAL)
    result = run_revision(store, Policy.B0, revision)
    store.expose("consume", Exposure(revision, result.artifacts[-1], cached=True))
    audit = audit_revision(store, revision, result.artifacts)
    assert not audit.final_satisfied
    assert audit.actual_use_events == 7
    assert audit.invalid_use_events == 0
    assert audit.lineage_violations == 1
