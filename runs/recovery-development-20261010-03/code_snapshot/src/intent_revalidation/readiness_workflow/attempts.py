"""Verify actual composition attempts, costs and creation provenance."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from src.intent_revalidation.fixtures import field, mapping, string
from src.intent_revalidation.model import decode_json, digest
from src.intent_revalidation.report_workflow.inputs import count

if TYPE_CHECKING:
    from .execution import ArmRun, CaseInputs

ATTEMPT_ACTIONS: Final = ("start", "complete")


@dataclass(frozen=True, slots=True)
class AttemptAudit:
    """Started work is counted even if its completion record is missing."""

    started: int
    completed: int
    violations: int


def audit_attempts(run: ArmRun, inputs: CaseInputs) -> AttemptAudit:
    """Bind completion evidence to actual inputs, current code and publication bytes."""
    try:
        lines = (run.store.root / "composition-attempts.jsonl").read_text().splitlines()
    except FileNotFoundError:
        return AttemptAudit(0, 0, 1)
    records = [mapping(decode_json(line)) for line in lines]
    starts = [row for row in records if field(row, "action") == "start"]
    completions = [row for row in records if field(row, "action") == "complete"]
    violations = int([field(row, "action") for row in records] != list(ATTEMPT_ACTIONS))
    by_id = {string(field(row, "attempt_id")): row for row in starts}
    violations += int(len(by_id) != len(starts))
    for row in starts:
        violations += int(field(row, "revision") != run.revision.revision_id)
        _ = count(field(row, "started_ns"))
    expected = {
        "revision": run.revision.revision_id,
        "input_report_sha256": digest(run.numeric.artifacts[-1].path.read_bytes()),
        "facts_sha256": inputs.snapshot.sha256,
        "output_sha256": digest(run.document.read_bytes()),
        "code_sha256": digest(Path(__file__).with_name("composition.py").read_bytes()),
        "environment_sha256": run.store.context.env_hash,
    }
    for row in completions:
        beginning = by_id.get(string(field(row, "attempt_id")))
        violations += int(beginning is None)
        if beginning is not None:
            violations += int(
                count(field(row, "completed_ns")) < count(field(beginning, "started_ns"))
            )
        violations += sum(field(row, key) != value for key, value in expected.items())
    return AttemptAudit(len(starts), len(completions), violations)
