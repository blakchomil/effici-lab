"""Generate immutable bytes under the original attempt revision and input snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .model import Artifact, ArtifactId, AttemptId, Context, Revision, Task, digest
from .pipeline import cache_key, execute, extension

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class Attempt:
    """A start record stays tied to r0 even if it completes after the change to r1."""

    id: AttemptId
    task: Task
    revision: Revision
    inputs: tuple[Artifact, ...]
    phase: str
    started_ns: int


def execute_attempt(attempt: Attempt, root: Path, context: Context) -> Artifact:
    content = execute(attempt.task, attempt.revision.requirements, context, attempt.inputs)
    identifier = ArtifactId(f"a-{attempt.id}")
    path = (
        root / "artifacts" / f"{identifier}{extension(attempt.task, attempt.revision.requirements)}"
    )
    with path.open("xb") as stream:
        _ = stream.write(content)
    return Artifact(
        identifier,
        attempt.task,
        path,
        digest(content),
        attempt.id,
        attempt.revision.id,
        attempt.revision.requirements,
        tuple(item.id for item in attempt.inputs),
        tuple(item.sha256 for item in attempt.inputs),
        context.source_sha256,
        context.code_sha256,
        context.environment_sha256,
        context.contract_version,
        cache_key(attempt.task, attempt.revision.requirements, context, attempt.inputs),
    )
