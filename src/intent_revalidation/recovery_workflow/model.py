"""Event identities, fault evidence and measured recovery outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, override

from src.intent_revalidation.fixtures import mapping
from src.intent_revalidation.report_workflow.outcomes import Outcome as ReportOutcome

if TYPE_CHECKING:
    from src.intent_revalidation.model import Json
    from src.intent_revalidation.report_workflow.model import Revision


class Fault(StrEnum):
    """Public deterministic fault rules shared by every policy."""

    NONE = "none"
    DELETE_NEWEST_SUMMARY = "delete_newest_summary"
    DELETE_ALL_SUMMARY = "delete_all_summary"
    CORRUPT_ALL_RENDER = "corrupt_all_render"
    DELETE_NEWEST_SELECT = "delete_newest_select"


@dataclass(frozen=True, slots=True)
class Event:
    """One requirement revision and its preceding fault injection."""

    revision: Revision
    fault: Fault

    @property
    def event_id(self) -> str:
        return self.revision.revision_id

    def to_json(self) -> Json:
        return {
            "event": self.event_id,
            "requirements": self.revision.requirements.to_json(),
            "fault": self.fault.value,
        }


@dataclass(frozen=True, slots=True)
class FaultTarget:
    """A target's immutable preimage and observed damage, including absent candidates."""

    artifact_id: str
    path: str
    archive_path: str | None
    pre_sha256: str | None
    post_sha256: str | None
    action: str
    declared_sha256: str
    generation_revision: str

    def to_json(self) -> Json:
        return {
            "artifact_id": self.artifact_id,
            "path": self.path,
            "archive_path": self.archive_path,
            "pre_sha256": self.pre_sha256,
            "post_sha256": self.post_sha256,
            "action": self.action,
            "declared_sha256": self.declared_sha256,
            "generation_revision": self.generation_revision,
        }


@dataclass(frozen=True, slots=True)
class FaultResult:
    """Measured injection work, distinct from policy executions and checks."""

    targets: tuple[FaultTarget, ...]
    duration_ns: int
    eligible_ids: tuple[str, ...]

    def to_json(self) -> Json:
        return {
            "targets": [item.to_json() for item in self.targets],
            "eligible_ids": list(self.eligible_ids),
            "duration_ns": self.duration_ns,
            "workflow_executions": 0,
        }


@dataclass(frozen=True, slots=True)
class Outcome(ReportOutcome):
    """Existing policy measurements plus the repeat and fault boundary evidence."""

    repeat: int
    position: int
    event: Event
    fault: FaultResult
    preparation_ns: int

    @override
    def to_json(self) -> Json:
        return {
            **mapping(ReportOutcome.to_json(self)),
            "repeat": self.repeat,
            "position": self.position,
            "event": self.event.event_id,
            "audit_scope": "current revision before subsequent faults or pointer changes",
            "selected_snapshot": str(
                self.result.artifacts[-1].path.parent.parent
                / "events"
                / self.event.event_id
                / "selected-artifacts"
            ),
            "fault": self.fault.to_json(),
            "preparation_ns": self.preparation_ns,
            "policy_started_ns": self.result.started_ns,
            "policy_finished_ns": self.result.finished_ns,
        }
