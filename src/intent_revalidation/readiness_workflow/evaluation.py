"""Independent audit of visible readiness evidence and preserved numeric results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.intent_revalidation.model import Check, InputError, Validity, decode_json, digest
from src.intent_revalidation.report_workflow.evaluation import source_oracle

from .model import FACT_KEYS

if TYPE_CHECKING:
    from src.intent_revalidation.report_workflow.model import Context, ReportRequirements

    from .model import Snapshot


@dataclass(frozen=True, slots=True)
class NumericContract:
    """Original numerical requirements and evidence, separate from composition."""

    requirements: ReportRequirements
    context: Context


def _table(lines: list[str], width: int) -> tuple[tuple[str, ...], ...]:
    rows: list[tuple[str, ...]] = []
    for line in lines:
        cells = tuple(cell.strip() for cell in line.split("|"))
        if len(cells) != width + 2 or cells[0] or cells[-1]:
            raise InputError("document", "malformed Markdown evidence table")
        rows.append(cells[1:-1])
    return tuple(rows)


def _numeric_matches(content: str, contract: NumericContract) -> bool:
    target, context = contract.requirements, contract.context
    oracle = source_oracle(target, context)
    lines = [line for line in content.splitlines() if line]
    if lines[:3] != [
        f"# {target.title}",
        f"Source SHA256: {context.source.sha256}",
        f"Cases: {', '.join(target.case_ids)}",
    ]:
        return False
    return _table(lines[3:], len(target.columns)) == (
        tuple(column.value for column in target.columns),
        tuple("---" for _ in target.columns),
        *oracle.rows,
    )


def _readiness_matches(content: str, snapshot: Snapshot, source_hash: str) -> bool:
    lines = [line for line in content.splitlines() if line]
    if lines[:5] != [
        "# Support readiness",
        f"Snapshot UTC: {snapshot.captured_at}",
        f"Repository revision: {snapshot.repository_revision}",
        f"Source SHA256: {source_hash}",
        f"Facts SHA256: {snapshot.sha256}",
    ]:
        return False
    if lines[-1:] != ["## Preserved experiment report"]:
        return False
    expected = (
        ("key", "value", "evidence"),
        ("---", "---", "---"),
        *((fact.key, fact.value, fact.evidence) for fact in snapshot.facts),
    )
    return _table(lines[5:-1], 3) == expected


def audit_document(content: bytes, snapshot: Snapshot, contract: NumericContract) -> Check:
    """Reject unsupported visible claims and independently reconstruct numeric cells."""
    if digest(snapshot.content) != snapshot.sha256:
        return Check(Validity.INVALID, "snapshot fingerprint mismatch")
    if len(snapshot.facts) != len(FACT_KEYS) or {fact.key for fact in snapshot.facts} != set(
        FACT_KEYS
    ):
        return Check(Validity.INVALID, "snapshot must contain all five readiness facts")
    try:
        if decode_json(snapshot.content.decode("utf-8")) != {
            "captured_at": snapshot.captured_at,
            "repository_revision": snapshot.repository_revision,
            "facts": [fact.to_json() for fact in snapshot.facts],
        }:
            return Check(Validity.INVALID, "snapshot fields differ from frozen evidence")
        text = content.decode("utf-8")
        prefix, numeric = text.split("<!-- numeric:start -->\n")
        numeric, suffix = numeric.split("<!-- numeric:end -->\n")
        valid = (
            not suffix
            and _readiness_matches(prefix, snapshot, contract.context.source.sha256)
            and _numeric_matches(numeric, contract)
        )
    except (InputError, ValueError, UnicodeError) as error:
        return Check(Validity.INVALID, f"independent document parse failed: {error}")
    return Check(
        Validity.VALID if valid else Validity.INVALID,
        "visible facts and source-derived numbers match" if valid else "document evidence mismatch",
    )
