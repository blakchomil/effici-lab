"""Immutable domain records and canonical serialization for the four-stage workflow."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final, NewType, Protocol, assert_never, override

if TYPE_CHECKING:
    from pathlib import Path

type Json = bool | int | float | str | list[Json] | dict[str, Json] | None
type JsonObject = dict[str, Json]
ArtifactId = NewType("ArtifactId", str)
AttemptId = NewType("AttemptId", str)
RevisionId = NewType("RevisionId", str)


class JsonDecoder(Protocol):
    """Constrain the stdlib JSON boundary to JSON values."""

    def __call__(self, source: str, /) -> Json: ...


decode_json: Final[JsonDecoder] = json.loads


def canonical(value: Json) -> bytes:
    """Return deterministic UTF-8 JSON bytes."""
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode()


def digest(content: bytes) -> str:
    """Compute the actual byte fingerprint."""
    return hashlib.sha256(content).hexdigest()


class Task(StrEnum):
    """Logical task identity, independent of its execution attempts."""

    LOAD = "load"
    NORMALIZE = "normalize"
    AGGREGATE = "aggregate"
    RENDER = "render"


TASKS: Final = tuple(Task)
ROLES: Final = {
    Task.LOAD: "raw_records",
    Task.NORMALIZE: "normalized_records",
    Task.AGGREGATE: "aggregate",
    Task.RENDER: "report",
}
CONTRACT_VERSION: Final = "phase1-v1"


@dataclass(frozen=True, slots=True)
class InputError(Exception):
    """A named malformed input at a file or CLI boundary."""

    field: str
    detail: str

    @override
    def __str__(self) -> str:
        return f"{self.field}: {self.detail}"


@dataclass(frozen=True, slots=True)
class Requirements:
    """The supported structured requirement state; revisions carry identity separately."""

    dataset_id: str
    start: str
    end: str
    output_format: str
    language: str
    title: str

    def to_json(self) -> Json:
        """Serialize the declared contract without revision or natural-language text."""
        return {
            "dataset_id": self.dataset_id,
            "period": {"start_inclusive": self.start, "end_exclusive": self.end},
            "group_by": ["category"],
            "metric": {"operation": "sum", "field": "amount_cents", "unit": "cents"},
            "output": {
                "format": self.output_format,
                "language": self.language,
                "title": self.title,
            },
        }

    def relevant(self, task: Task) -> Json:
        """Project only fields directly consumed by a task for granular cache keys."""
        match task:
            case Task.LOAD:
                return {"dataset_id": self.dataset_id}
            case Task.NORMALIZE:
                return {}
            case Task.AGGREGATE:
                return {
                    "start": self.start,
                    "end": self.end,
                    "group_by": ["category"],
                    "operation": "sum",
                    "field": "amount_cents",
                    "unit": "cents",
                }
            case Task.RENDER:
                return {
                    "format": self.output_format,
                    "language": self.language,
                    "title": self.title,
                }
            case unreachable:
                assert_never(unreachable)


@dataclass(frozen=True, slots=True)
class Revision:
    """An immutable requirement revision."""

    id: RevisionId
    parent_id: RevisionId | None
    requirements: Requirements
    change: str

    def to_json(self) -> Json:
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "requirements": self.requirements.to_json(),
            "change": self.change,
        }


@dataclass(frozen=True, slots=True)
class Context:
    """Fixed source, implementation, environment and role-contract fingerprints."""

    dataset_id: str
    source: bytes
    source_sha256: str
    code_sha256: str
    environment_sha256: str
    contract_version: str = CONTRACT_VERSION


@dataclass(frozen=True, slots=True)
class Artifact:
    """An immutable result whose bytes remain separate from execution identity."""

    id: ArtifactId
    task: Task
    path: Path
    sha256: str
    attempt_id: AttemptId
    revision_id: RevisionId
    requirements: Requirements
    input_ids: tuple[ArtifactId, ...]
    input_hashes: tuple[str, ...]
    source_sha256: str
    code_sha256: str
    environment_sha256: str
    contract_version: str
    cache_key: str

    def to_json(self) -> Json:
        """Expose provenance without altering the original generation revision."""
        return {
            "id": self.id,
            "task_id": self.task.value,
            "role": ROLES[self.task],
            "path": str(self.path),
            "sha256": self.sha256,
            "attempt_id": self.attempt_id,
            "revision_id": self.revision_id,
            "requirements": self.requirements.to_json(),
            "input_ids": list(self.input_ids),
            "input_hashes": list(self.input_hashes),
            "source_sha256": self.source_sha256,
            "code_sha256": self.code_sha256,
            "environment_sha256": self.environment_sha256,
            "contract_version": self.contract_version,
            "cache_key": self.cache_key,
        }


class Validity(StrEnum):
    """Validity is distinct from the policy action."""

    VALID = "valid"
    INVALID = "invalid"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Check:
    """Role-specific executable evidence."""

    validity: Validity
    reason: str

    def to_json(self) -> Json:
        return {"validity": self.validity.value, "reason": self.reason}


@dataclass(frozen=True, slots=True)
class Measurement:
    """Operation identity and measured nanoseconds, separate from validity evidence."""

    kind: str
    duration_ns: int
