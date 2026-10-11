from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from src.intent_revalidation.governance_workflow.reporting import write_report
from src.intent_revalidation.model import Json, JsonObject, decode_json

if TYPE_CHECKING:
    from pathlib import Path


def _metrics(rows: list[Json]) -> JsonObject:
    return {"study": "test", "rows": rows, "arms": [], "limitations": []}


def test_missing_lifecycle_evidence_is_not_a_pass(tmp_path: Path) -> None:
    # Given successful initial work and an unauditable compaction with good final bytes.
    rows: list[Json] = [
        {
            "arm": "G0",
            "phase": "initial",
            "eligible": True,
            "audit": {"satisfied": True},
            "error": None,
        },
        {
            "arm": "G0",
            "phase": "compact",
            "eligible": False,
            "audit": {"satisfied": True},
            "error": None,
        },
    ]
    # When the report is written.
    write_report(tmp_path, _metrics(rows))
    # Then initial completion never contributes to the lifecycle pass count.
    report = (tmp_path / "report.md").read_text()
    assert "| G0 | 0 / 3 | 0 | 0 | 3 |" in report
    assert "| G0 | compact | UNEVALUATED |" in report


def test_unsuccessful_audit_and_process_evidence_are_preserved(tmp_path: Path) -> None:
    # Given a completed transition with a failed audit and an execution error.
    rows: list[Json] = [
        {
            "arm": "G2",
            "phase": "delegation",
            "eligible": True,
            "audit": {"satisfied": False, "invalid_publication_snapshots": 4},
            "transition_evidence": {"subagent_start_ids": ["worker"]},
            "error": "worker exited 1",
        }
    ]
    metrics = _metrics(rows)
    metrics["arms"] = [{"arm": "G2", "processes": [{"returncode": 1}]}]
    # When the report is written.
    write_report(tmp_path, metrics)
    # Then failure is counted and exact source evidence remains recoverable.
    report = (tmp_path / "report.md").read_text()
    assert "| G2 | 1 / 3 | 0 | 1 | 2 |" in report
    details = decode_json(report.split("````json\n", 1)[1].split("\n````", 1)[0])
    assert details == {"rows": rows, "arms": metrics["arms"]}


def test_existing_report_cannot_be_overwritten(tmp_path: Path) -> None:
    # Given an immutable report from a previous attempt.
    original = b"previous evidence\n"
    _ = (tmp_path / "report.md").write_bytes(original)
    # When the same destination is reused.
    with pytest.raises(FileExistsError):
        write_report(tmp_path, _metrics([]))
    # Then earlier evidence is untouched.
    assert (tmp_path / "report.md").read_bytes() == original
