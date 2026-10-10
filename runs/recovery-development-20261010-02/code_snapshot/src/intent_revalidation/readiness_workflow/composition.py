"""Compose frozen readiness facts around an unchanged experiment report."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.intent_revalidation.model import InputError

if TYPE_CHECKING:
    from .model import Snapshot


def compose(numeric_report: bytes, snapshot: Snapshot, source_sha256: str) -> bytes:
    """Embed a newline-terminated report verbatim after parsed snapshot facts."""
    if not numeric_report.endswith(b"\n"):
        raise InputError("numeric_report", "expected a trailing newline")
    header = (
        "# Support readiness\n\n"
        f"Snapshot UTC: {snapshot.captured_at}\n"
        f"Repository revision: {snapshot.repository_revision}\n"
        f"Source SHA256: {source_sha256}\n"
        f"Facts SHA256: {snapshot.sha256}\n\n"
        "| key | value | evidence |\n"
        "| --- | --- | --- |\n"
    )
    rows = "".join(f"| {fact.key} | {fact.value} | {fact.evidence} |\n" for fact in snapshot.facts)
    prefix = header + rows + "\n## Preserved experiment report\n\n<!-- numeric:start -->\n"
    return prefix.encode("utf-8") + numeric_report + b"<!-- numeric:end -->\n"
