"""Append-only attempts and artifacts; only the publication pointer is mutable."""

from __future__ import annotations

import shutil
import time
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, assert_never

from src.intent_revalidation.model import ArtifactId, Json, canonical, digest

from .model import Artifact, Context, Revision, Step
from .operations import render, select_rows, summarize

if TYPE_CHECKING:
    from pathlib import Path


class Store:
    """Accumulate historical artifacts and measured operations throughout revisions."""

    def __init__(self, root: Path, context: Context) -> None:
        self.root: Path = root
        self.context: Context = context
        self.artifacts: list[Artifact] = []
        self.counts: dict[str, int] = {}
        self.durations: dict[str, int] = {}

    @property
    def cache(self) -> tuple[Artifact, ...]:
        return tuple(self.artifacts)

    def record(self, name: str, value: Json) -> None:
        with (self.root / name).open("ab") as stream:
            _ = stream.write(canonical(value))

    def measure(self, name: str, started: int) -> None:
        self.counts[name] = self.counts.get(name, 0) + 1
        self.durations[name] = self.durations.get(name, 0) + time.perf_counter_ns() - started

    def hash_bytes(self, content: bytes) -> str:
        started = time.perf_counter_ns()
        result = digest(content)
        self.measure("hash_operations", started)
        return result

    def key(self, request: Request) -> str:
        started = time.perf_counter_ns()
        result = cache_key(request, self.context)
        self.measure("key_computations", started)
        return result

    def clone(self, destination: Path) -> Store:
        _ = shutil.copytree(self.root, destination)
        artifacts = [
            replace(item, path=destination / item.path.relative_to(self.root))
            for item in self.artifacts
        ]
        result = Store(destination, self.context)
        result.artifacts.extend(artifacts)
        result.record(
            "clones.jsonl",
            {"source": str(self.root), "artifacts": [item.to_json() for item in artifacts]},
        )
        return result

    def expose(self, action: str, exposure: Exposure) -> None:
        started = time.perf_counter_ns()
        self.record(
            "events.jsonl",
            {
                "action": action,
                "revision": exposure.revision.revision_id,
                "artifact_id": exposure.artifact.artifact_id,
                "step": exposure.artifact.step.value,
                "cached": exposure.cached,
                "time_ns": started,
            },
        )
        self.measure(action, started)


@dataclass(frozen=True, slots=True)
class Exposure:
    """One actual binding, input consumption or publication under a revision."""

    revision: Revision
    artifact: Artifact
    cached: bool


@dataclass(frozen=True, slots=True)
class Request:
    """The complete input lineage for one stage selection."""

    step: Step
    revision: Revision
    predecessor: Artifact | None

    def input_bytes(self, context: Context) -> bytes:
        if self.predecessor is None:
            return context.source.content
        return self.predecessor.path.read_bytes()


def cache_key(request: Request, context: Context) -> str:
    return digest(
        canonical(
            {
                "step": request.step.value,
                "requirements": request.revision.requirements.relevant(request.step),
                "input_hash": digest(request.input_bytes(context)),
                "source_hash": context.source.sha256,
                "code_hash": context.code_hash(request.step),
                "env_hash": context.env_hash,
                "contract_version": context.contract_version,
            }
        )
    )


def execute(store: Store, request: Request) -> Artifact:
    started = time.perf_counter_ns()
    artifact_id = ArtifactId(f"a-{len(store.artifacts):06d}-{request.step.value}")
    metadata: Json = {
        "attempt_id": artifact_id,
        "revision": request.revision.revision_id,
        "step": request.step.value,
        "time_ns": started,
    }
    store.record("attempts.jsonl", {"action": "start", "attempt": metadata})
    content = request.input_bytes(store.context)
    match request.step:
        case Step.SELECT:
            produced = select_rows(request.revision.requirements, store.context)
        case Step.SUMMARY:
            produced = summarize(content)
        case Step.RENDER:
            produced = render(content, request.revision.requirements)
        case unreachable:
            assert_never(unreachable)
    suffix = ".md" if request.step == Step.RENDER else ".json"
    path = store.root / "artifacts" / (artifact_id + suffix)
    with path.open("xb") as stream:
        _ = stream.write(produced)
    artifact = Artifact(
        artifact_id,
        request.step,
        path,
        store.hash_bytes(produced),
        store.hash_bytes(content),
        store.key(request),
        request.revision.revision_id,
        request.revision.requirements,
        store.context.code_hash(request.step),
        store.context.env_hash,
        store.context.source.sha256,
        store.context.contract_version,
    )
    store.artifacts.append(artifact)
    store.record("artifacts.jsonl", artifact.to_json())
    store.record(
        "attempts.jsonl",
        {
            "action": "complete",
            "attempt": metadata,
            "artifact_id": artifact_id,
            "completed_ns": time.perf_counter_ns(),
        },
    )
    store.measure("executions", started)
    return artifact
