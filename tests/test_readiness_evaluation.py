from dataclasses import replace
from typing import Final

import pytest

from src.intent_revalidation.model import Json, Validity, canonical, digest
from src.intent_revalidation.readiness_workflow.evaluation import NumericContract, audit_document
from src.intent_revalidation.readiness_workflow.model import Fact, Snapshot
from src.intent_revalidation.report_workflow.model import (
    Column,
    Context,
    ReportRequirements,
    Source,
)

FACTS: Final = (
    Fact("license", "MIT", "LICENSE"),
    Fact("ci", "success", "https://example.test/actions/1"),
    Fact("release", "v0.1.0 prerelease", "https://example.test/releases/v0.1.0"),
    Fact("external_reproduction", "unestablished", "https://example.test/issues/2"),
    Fact("ai_advantage", "unestablished", "RESEARCH.md"),
)


@pytest.fixture
def snapshot() -> Snapshot:
    raw = canonical(
        {
            "captured_at": "2026-10-10T08:00:00Z",
            "repository_revision": "a" * 40,
            "facts": [fact.to_json() for fact in FACTS],
        }
    )
    return Snapshot("2026-10-10T08:00:00Z", "a" * 40, FACTS, raw, digest(raw))


@pytest.fixture
def contract() -> NumericContract:
    rows: list[Json] = [
        {
            "case_id": "D1",
            "policy": policy,
            "audit": {"final_satisfied": valid, "invalid_reuse_events": invalid},
            "operation_counts": {"policy_executions": executions},
        }
        for policy, valid, invalid, executions in (
            ("B0", True, 0, 4),
            ("B1", False, 1, 2),
            ("B2", True, 0, 0),
        )
    ]
    raw = canonical(rows)
    # Empty parsed rows force the evaluator to consume original metrics bytes.
    context = Context(Source(raw, digest(raw), ()), ("a", "b", "c"), "env", "v1")
    return NumericContract(ReportRequirements(("D1",), "Original report", tuple(Column)), context)


@pytest.fixture
def document(snapshot: Snapshot, contract: NumericContract) -> bytes:
    return (
        "# Support readiness\n\n"
        f"Snapshot UTC: {snapshot.captured_at}\n"
        f"Repository revision: {snapshot.repository_revision}\n"
        f"Source SHA256: {contract.context.source.sha256}\n"
        f"Facts SHA256: {snapshot.sha256}\n\n"
        "| key | value | evidence |\n"
        "| --- | --- | --- |\n"
        "| license | MIT | LICENSE |\n"
        "| ci | success | https://example.test/actions/1 |\n"
        "| release | v0.1.0 prerelease | https://example.test/releases/v0.1.0 |\n"
        "| external_reproduction | unestablished | https://example.test/issues/2 |\n"
        "| ai_advantage | unestablished | RESEARCH.md |\n\n"
        "## Preserved experiment report\n\n"
        "<!-- numeric:start -->\n"
        "# Original report\n\n"
        f"Source SHA256: {contract.context.source.sha256}\n"
        "Cases: D1\n\n"
        "| policy | valid_cases | executions | invalid_reuse |\n"
        "| --- | --- | --- | --- |\n"
        "| B0 | 1/1 | 4 | 0 |\n"
        "| B1 | 0/1 | 2 | 1 |\n"
        "| B2 | 1/1 | 0 | 0 |\n"
        "<!-- numeric:end -->\n"
    ).encode()


def test_accepts_original_evidence_when_parsed_source_rows_are_empty(
    document: bytes, snapshot: Snapshot, contract: NumericContract
) -> None:
    # Given a hand-written document and original metrics, without parsed rows.
    # When the independent evaluator audits the visible document.
    check = audit_document(document, snapshot, contract)
    # Then source-derived values are sufficient to establish validity.
    assert check.validity == Validity.VALID


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (b"| license | MIT |", b"| license | Apache-2.0 |"),
        (b"| ci | success |", b"| ci | pending |"),
        (b"| release | v0.1.0 prerelease |", b"| release | v1.0.0 stable |"),
        (b"| license | MIT | LICENSE |", b"| license | MIT | fabricated |"),
        (b"| key | value | evidence |", b"| key | value | claim |"),
        (b"| ai_advantage | unestablished | RESEARCH.md |\n", b""),
        (b"| external_reproduction | unestablished | https://example.test/issues/2 |\n", b""),
        (b"| ai_advantage | unestablished |", b"| ai_advantage | established |"),
        (b"| external_reproduction | unestablished |", b"| external_reproduction | established |"),
        (b"Repository revision: " + b"a" * 40, b"Repository revision: " + b"b" * 40),
        (b"Snapshot UTC: 2026-10-10T08:00:00Z", b"Snapshot UTC: 2026-10-09T08:00:00Z"),
        (b"Facts SHA256: ", b"Facts SHA256: wrong"),
        (b"Source SHA256: ", b"Source SHA256: wrong"),
        (b"# Original report\n\nSource SHA256: ", b"# Original report\n\nSource SHA256: wrong"),
        (b"# Original report", b"# Another report"),
        (b"Cases: D1", b"Cases: D2"),
        (b"| policy | valid_cases | executions | invalid_reuse |", b"| policy | count |"),
        (b"| B0 | 1/1 | 4 | 0 |", b"| B0 | 1/1 | 3 | 0 |"),
        (b"| B1 | 0/1 | 2 | 1 |", b"| B1 | 1/1 | 2 | 0 |"),
        (b"| B2 | 1/1 | 0 | 0 |\n", b""),
        (b"<!-- numeric:start -->", b"<!-- numeric:missing -->"),
        (b"<!-- numeric:end -->", b"<!-- numeric:end -->\nAI advantage is established."),
        (b"## Preserved experiment report", b"AI wins.\n## Preserved experiment report"),
        (
            b"| license | MIT | LICENSE |",
            b"| license | MIT | LICENSE |\n| support | ready | none |",
        ),
    ],
)
def test_rejects_changed_visible_evidence(
    document: bytes, snapshot: Snapshot, contract: NumericContract, before: bytes, after: bytes
) -> None:
    # Given one mutated structural field in an otherwise valid public document.
    corrupted = document.replace(before, after)
    assert corrupted != document
    # When the visible result is audited against original evidence.
    check = audit_document(corrupted, snapshot, contract)
    # Then the unsupported result is rejected.
    assert check.validity == Validity.INVALID


@pytest.mark.parametrize("fact_index", range(len(FACTS)))
def test_rejects_forged_typed_fact_even_when_document_agrees(
    document: bytes, snapshot: Snapshot, contract: NumericContract, fact_index: int
) -> None:
    # Given typed facts and visible text forged together, with frozen bytes unchanged.
    original = snapshot.facts[fact_index]
    forged = replace(original, value="unsupported")
    facts = tuple(forged if fact == original else fact for fact in snapshot.facts)
    changed = replace(snapshot, facts=facts)
    corrupted = document.replace(
        f"| {original.key} | {original.value} |".encode(),
        f"| {forged.key} | {forged.value} |".encode(),
    )
    # When the document is checked against the actual frozen snapshot bytes.
    check = audit_document(corrupted, changed, contract)
    # Then synchronized metadata forgery still fails.
    assert check.validity == Validity.INVALID


def test_rejects_changed_metrics_without_matching_fingerprint(
    document: bytes, snapshot: Snapshot, contract: NumericContract
) -> None:
    # Given original metrics changed after recording the source hash.
    source = replace(contract.context.source, content=b"[]")
    changed = replace(contract, context=replace(contract.context, source=source))
    # When source-derived evidence is reconstructed.
    check = audit_document(document, snapshot, changed)
    # Then the source fingerprint mismatch fails closed.
    assert check.validity == Validity.INVALID


def test_rejects_missing_fact_even_when_snapshot_and_document_agree(
    document: bytes, snapshot: Snapshot, contract: NumericContract
) -> None:
    # Given an incomplete snapshot and visible table with the same omission.
    changed = replace(snapshot, facts=snapshot.facts[:-1])
    corrupted = document.replace(b"| ai_advantage | unestablished | RESEARCH.md |\n", b"")
    # When the audit checks the required evidence set.
    check = audit_document(corrupted, changed, contract)
    # Then the missing uncertainty cannot disappear from the result.
    assert check.validity == Validity.INVALID


def test_rejects_malformed_utf8(
    document: bytes, snapshot: Snapshot, contract: NumericContract
) -> None:
    # Given an undecodable public result.
    corrupted = document + b"\xff"
    # When the result crosses the audit boundary.
    check = audit_document(corrupted, snapshot, contract)
    # Then decoding failure becomes an invalid assessment, not a crash.
    assert check.validity == Validity.INVALID


def test_rejects_changed_snapshot_bytes(
    document: bytes, snapshot: Snapshot, contract: NumericContract
) -> None:
    # Given snapshot content tampered after its fingerprint was recorded.
    corrupted = replace(snapshot, content=snapshot.content + b" ")
    # When the document is audited with that evidence.
    check = audit_document(document, corrupted, contract)
    # Then the evidence fingerprint mismatch invalidates the result.
    assert check.validity == Validity.INVALID


def test_rejects_changed_original_metrics_even_when_rehashed(
    document: bytes, snapshot: Snapshot, contract: NumericContract
) -> None:
    # Given new original metrics and matching source hashes, but stale visible counts.
    raw = contract.context.source.content.replace(
        b'"policy_executions":4', b'"policy_executions":9'
    )
    source = Source(raw, digest(raw), ())
    changed = replace(contract, context=replace(contract.context, source=source))
    stale = document.replace(contract.context.source.sha256.encode(), source.sha256.encode())
    # When the report is checked independently from the supplied hash metadata.
    check = audit_document(stale, snapshot, changed)
    # Then numerical cells must reflect the actual new bytes.
    assert check.validity == Validity.INVALID
