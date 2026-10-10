"""Frozen identities and contracts for the report revision experiment."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, assert_never

from src.intent_revalidation.model import ArtifactId, InputError, Json, RevisionId

if TYPE_CHECKING:
    from pathlib import Path

    from src.intent_revalidation.policies import Policy


class Step(StrEnum):
    """The three actual report-producing operations."""

    SELECT = "select"
    SUMMARY = "summary"
    RENDER = "render"


class Column(StrEnum):
    """Supported report fields, each included exactly once."""

    POLICY = "policy"
    VALID_CASES = "valid_cases"
    EXECUTIONS = "executions"
    INVALID_REUSE = "invalid_reuse"


@dataclass(frozen=True, slots=True)
class ReportRequirements:
    """A complete validated revision of the presentation and selection."""

    case_ids: tuple[str, ...]
    title: str
    columns: tuple[Column, ...]

    def __post_init__(self) -> None:
        """Reject ambiguous case selections and unsafe Markdown before execution."""
        if not self.case_ids or self.case_ids != tuple(sorted(set(self.case_ids))):
            raise InputError("case_ids", "expected nonempty sorted unique IDs")
        if any(not item or not item.isalnum() for item in self.case_ids):
            raise InputError("case_ids", "expected alphanumeric IDs")
        if not self.title.strip() or any(char in self.title for char in "\n\r|<>`*_[]\\"):
            raise InputError("title", "expected nonempty plain single-line Markdown title")
        if len(self.columns) != len(Column) or set(self.columns) != set(Column):
            raise InputError("columns", "expected a full permutation")

    def to_json(self) -> Json:
        return {
            "case_ids": list(self.case_ids),
            "title": self.title,
            "columns": [item.value for item in self.columns],
        }

    def relevant(self, step: Step) -> Json:
        match step:
            case Step.SELECT:
                return {"case_ids": list(self.case_ids)}
            case Step.SUMMARY:
                return {}
            case Step.RENDER:
                return {"title": self.title, "columns": [item.value for item in self.columns]}
            case unreachable:
                assert_never(unreachable)


@dataclass(frozen=True, slots=True)
class MetricRow:
    """Only the observed Phase 1 fields consumed by this workflow."""

    case_id: str
    policy: Policy
    valid: bool
    executions: int
    invalid_reuse: int

    def to_json(self) -> Json:
        return {
            "case_id": self.case_id,
            "policy": self.policy.value,
            "valid": self.valid,
            "executions": self.executions,
            "invalid_reuse": self.invalid_reuse,
        }


@dataclass(frozen=True, slots=True)
class Source:
    """Original immutable metrics bytes and parsed observed rows."""

    content: bytes
    sha256: str
    rows: tuple[MetricRow, ...]


@dataclass(frozen=True, slots=True)
class Context:
    """Actual stage dependencies and source identity used by all policies."""

    source: Source
    fingerprints: tuple[str, ...]
    env_hash: str
    contract_version: str

    def code_hash(self, step: Step) -> str:
        return self.fingerprints[tuple(Step).index(step)]


@dataclass(frozen=True, slots=True)
class Revision:
    """Generation identity separate from requirement content."""

    revision_id: RevisionId
    requirements: ReportRequirements


@dataclass(frozen=True, slots=True)
class Artifact:
    """Immutable provenance; an empty evidence field denotes unknown validity."""

    artifact_id: ArtifactId
    step: Step
    path: Path
    sha256: str
    input_hash: str
    key: str
    generation_revision: RevisionId
    requirements: ReportRequirements
    code_hash: str
    env_hash: str
    source_hash: str
    contract_version: str

    def to_json(self) -> Json:
        return {
            "artifact_id": self.artifact_id,
            "step": self.step.value,
            "path": str(self.path),
            "sha256": self.sha256,
            "input_hash": self.input_hash,
            "key": self.key,
            "generation_revision": self.generation_revision,
            "requirements": self.requirements.to_json(),
            "code_hash": self.code_hash,
            "env_hash": self.env_hash,
            "source_hash": self.source_hash,
            "contract_version": self.contract_version,
        }
