from dataclasses import replace
from pathlib import Path
from typing import Final

import pytest

from src.intent_revalidation.model import RevisionId, canonical
from src.intent_revalidation.policies import Policy
from src.intent_revalidation.report_workflow.audit import audit_revision
from src.intent_revalidation.report_workflow.cache import run_revision
from src.intent_revalidation.report_workflow.inputs import load_source
from src.intent_revalidation.report_workflow.model import Column, ReportRequirements, Revision
from src.intent_revalidation.report_workflow.operations import make_context
from src.intent_revalidation.report_workflow.storage import Exposure, Store

SOURCE: Final = Path(__file__).parents[1] / "runs/phase1-20261010-01/metrics.json"
INITIAL: Final = ReportRequirements(("D1", "D2", "D3", "D4", "D5"), "Original", tuple(Column))


@pytest.mark.parametrize("policy", [Policy.B1, Policy.B2])
def test_stale_publication_remains_invalid_after_pointer_restoration(
    tmp_path: Path, policy: Policy
) -> None:
    # Given a successful changed-title publication and an older original-title report.
    store = Store(tmp_path, make_context(load_source(SOURCE)))
    original = run_revision(store, Policy.B0, Revision(RevisionId("seed"), INITIAL))
    revision = Revision(RevisionId("changed"), replace(INITIAL, title="Changed"))
    result = run_revision(store, policy, revision)
    assert audit_revision(store, revision, result.artifacts).final_satisfied
    # When the old report is actually published, then the valid publication is restored.
    store.expose("publish", Exposure(revision, original.artifacts[-1], cached=True))
    _ = (store.root / "current.json").write_bytes(
        canonical(
            {"revision": revision.revision_id, "artifact_id": original.artifacts[-1].artifact_id}
        )
    )
    store.expose("publish", Exposure(revision, result.artifacts[-1], cached=False))
    _ = (store.root / "current.json").write_bytes(
        canonical(
            {"revision": revision.revision_id, "artifact_id": result.artifacts[-1].artifact_id}
        )
    )
    observed = audit_revision(store, revision, result.artifacts)
    # Then the complete history fails even though the pointer and final report are correct.
    assert result.artifacts[-1].path.read_text().splitlines()[0] == "# Changed"
    assert not observed.final_satisfied
    assert observed.publication_count == 3
    assert observed.invalid_use_events == observed.invalid_reuse_events == 1
    assert observed.lineage_violations == 1
    assert observed.actual_use_events == 8


@pytest.mark.parametrize("delete", [False, True])
def test_successful_audit_is_not_a_fresh_historical_audit_after_byte_loss(
    tmp_path: Path, *, delete: bool
) -> None:
    # Given a genuinely successful audit before any fault is introduced.
    store = Store(tmp_path, make_context(load_source(SOURCE)))
    revision = Revision(RevisionId("seed"), INITIAL)
    result = run_revision(store, Policy.B0, revision)
    previous = audit_revision(store, revision, result.artifacts)
    assert previous.final_satisfied
    # When the previously consumed SUMMARY disappears or its bytes change without metadata.
    summary = result.artifacts[1]
    if delete:
        summary.path.unlink()
    else:
        _ = summary.path.write_bytes(b"corrupted after the successful audit\n")
    observed = audit_revision(store, revision, result.artifacts)
    # Then a fresh audit rejects the historical exposure, despite the intact final report.
    assert result.artifacts[-1].path.read_text().splitlines()[0] == "# Original"
    assert previous.final_satisfied
    assert not observed.final_satisfied
    assert observed.invalid_use_events == 2
    assert observed.invalid_reuse_events == 0
