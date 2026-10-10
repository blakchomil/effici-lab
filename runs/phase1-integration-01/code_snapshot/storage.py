"""Append-only observed execution history and exclusive immutable artifact files."""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

from .model import (
    ROLES, Artifact, ArtifactId, AttemptId, Check, Context, InputError, Json,
    Revision, Task, canonical, digest,
)
from .pipeline import cache_key, execute, extension


@dataclass(frozen=True, slots=True)
class Attempt:
    """A start record remains tied to its original revision through late completion."""

    id: AttemptId
    task: Task
    revision: Revision
    inputs: tuple[Artifact, ...]
    phase: str
    started_ns: int


class Store:
    """Mutable execution accumulator; files and past records are never replaced."""

    def __init__(self, root: Path, context: Context) -> None:
        self.root: Path = root
        self.context: Context = context
        self.artifacts: list[Artifact] = []
        self.events: list[dict[str, Json]] = []
        self.sequence: int = 0
        self.active: dict[AttemptId, Attempt] = {}
        self.counters: dict[str, int] = {}
        self.durations_ns: dict[str, int] = {}
        self.cache_ids: set[ArtifactId] = set()
        self.root.mkdir(parents=True, exist_ok=False)
        (self.root / "artifacts").mkdir()

    def append(self, name: str, value: Json) -> None:
        with (self.root / name).open("ab") as stream:
            _ = stream.write(canonical(value))

    def emit(self, kind: str, **fields: Json) -> int:
        """Record actual local time separately from fixture replay sequence."""
        self.sequence += 1
        timestamp = time.perf_counter_ns()
        event: dict[str, Json] = {
            "event_id": f"e{self.sequence:06d}", "sequence": self.sequence,
            "time_utc": datetime.now(UTC).isoformat(), "monotonic_ns": timestamp,
            "type": kind, **fields,
        }
        self.events.append(event)
        self.append("events.jsonl", event)
        return timestamp

    def count(self, kind: str, duration_ns: int = 0) -> None:
        self.counters[kind] = self.counters.get(kind, 0) + 1
        self.durations_ns[kind] = self.durations_ns.get(kind, 0) + duration_ns

    def clone(self, root: Path) -> Store:
        """Copy the same initial cache and history into an isolated policy workspace."""
        clone = Store(root, self.context)
        for artifact in self.artifacts:
            path = clone.root / "artifacts" / artifact.path.name
            with path.open("xb") as stream:
                _ = stream.write(artifact.path.read_bytes())
            copied = replace(artifact, path=path)
            clone.artifacts.append(copied)
            clone.append("artifacts.jsonl", copied.to_json())
        for name in ("events.jsonl", "attempts.jsonl", "revisions.jsonl"):
            source = self.root / name
            if source.exists():
                with (clone.root / name).open("xb") as stream:
                    _ = stream.write(source.read_bytes())
        clone.events = [event.copy() for event in self.events]
        clone.sequence = self.sequence
        return clone

    def revise(self, revision: Revision) -> int:
        self.append("revisions.jsonl", revision.to_json())
        return self.emit("requirements_changed", revision_id=revision.id, parent_id=revision.parent_id,
                         requirements=revision.requirements.to_json(), change=revision.change)

    def start(self, task: Task, revision: Revision, inputs: tuple[Artifact, ...],
              phase: str, attempt_id: str | None = None) -> Attempt:
        identifier = AttemptId(attempt_id or f"{phase}-{task.value}-{self.sequence + 1:06d}")
        if identifier in self.active:
            raise InputError("attempt_id", f"already active: {identifier}")
        for artifact in inputs:
            _ = self.emit("artifact_consumed", artifact_id=artifact.id, revision_id=revision.id,
                          consumer_task=task.value, consumer_role=ROLES[artifact.task],
                          from_cache=artifact.id in self.cache_ids, phase=phase)
        started = self.emit("run_started", attempt_id=identifier, task_id=task.value,
                            revision_id=revision.id, input_ids=[item.id for item in inputs], phase=phase)
        attempt = Attempt(identifier, task, revision, inputs, phase, started)
        self.active[identifier] = attempt
        self.append("attempts.jsonl", {"id": identifier, "task_id": task.value,
            "revision_id": revision.id, "input_ids": [item.id for item in inputs],
            "started_ns": started, "status": "running", "phase": phase})
        return attempt

    def complete(self, attempt: Attempt) -> Artifact:
        compute_start = time.perf_counter_ns()
        try:
            content = execute(attempt.task, attempt.revision.requirements, self.context, attempt.inputs)
            identifier = ArtifactId(f"a-{attempt.id}")
            path = self.root / "artifacts" / f"{identifier}{extension(attempt.task, attempt.revision.requirements)}"
            with path.open("xb") as stream:
                _ = stream.write(content)
            artifact = Artifact(identifier, attempt.task, path, digest(content), attempt.id,
                attempt.revision.id, attempt.revision.requirements,
                tuple(item.id for item in attempt.inputs), tuple(item.sha256 for item in attempt.inputs),
                self.context.source_sha256, self.context.code_sha256, self.context.environment_sha256,
                self.context.contract_version,
                cache_key(attempt.task, attempt.revision.requirements, self.context, attempt.inputs))
        except (InputError, OSError, ValueError) as error:
            elapsed = time.perf_counter_ns() - compute_start
            self.count(f"{attempt.phase}_executions", elapsed)
            self.count("failed_attempts")
            self.append("attempts.jsonl", {"id": attempt.id, "revision_id": attempt.revision.id,
                "status": "failed", "error": str(error), "compute_ns": elapsed})
            _ = self.emit("run_failed", attempt_id=attempt.id, error=str(error))
            del self.active[attempt.id]
            raise
        elapsed = time.perf_counter_ns() - compute_start
        self.count(f"{attempt.phase}_executions", elapsed)
        self.artifacts.append(artifact)
        self.append("artifacts.jsonl", artifact.to_json())
        finished = self.emit("run_completed", attempt_id=attempt.id, task_id=attempt.task.value,
            started_revision_id=attempt.revision.id, artifact_id=artifact.id,
            produced_role=ROLES[attempt.task], phase=attempt.phase, compute_ns=elapsed)
        self.append("attempts.jsonl", {"id": attempt.id, "task_id": attempt.task.value,
            "revision_id": attempt.revision.id, "status": "completed", "phase": attempt.phase,
            "started_ns": attempt.started_ns, "finished_ns": finished, "compute_ns": elapsed,
            "artifact_id": artifact.id})
        del self.active[attempt.id]
        return artifact

    def assess(self, artifact: Artifact, revision: Revision, action: str, check: Check,
               duration_ns: int, kind: str) -> None:
        self.count(kind, duration_ns)
        self.append("assessments.jsonl", {
            "artifact_id": artifact.id, "target_revision_id": revision.id,
            "consumer_role": ROLES[artifact.task], "action": action,
            "validity": check.validity.value, "reason": check.reason,
            "check_kind": kind, "duration_ns": duration_ns,
        })
        _ = self.emit("artifact_assessed", artifact_id=artifact.id, revision_id=revision.id,
                      consumer_role=ROLES[artifact.task], action=action, validity=check.validity.value)

    def bind(self, artifact: Artifact, revision: Revision, action: str) -> None:
        started = time.perf_counter_ns()
        _ = self.emit("artifact_bound", artifact_id=artifact.id, revision_id=revision.id,
            consumer_role=ROLES[artifact.task], task_id=artifact.task.value,
            action=action, from_cache=artifact.id in self.cache_ids)
        self.count("binding_operations", time.perf_counter_ns() - started)

    def publish(self, artifacts: tuple[Artifact, ...], revision: Revision) -> int:
        """Replace only the current pointer; report and generation history stay immutable."""
        current: dict[str, Json] = {
            "revision_id": revision.id,
            "artifacts": {artifact.task.value: artifact.id for artifact in artifacts},
            "report_path": str(artifacts[-1].path),
        }
        _ = (self.root / "current.json").write_bytes(canonical(current))
        return self.emit("report_published", artifact_id=artifacts[-1].id,
            revision_id=revision.id, consumer_role="report", from_cache=artifacts[-1].id in self.cache_ids)
