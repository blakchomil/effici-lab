"""Audit actual report-workflow exposures independently of policy decisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, assert_never

from src.intent_revalidation.fixtures import field, mapping, string
from src.intent_revalidation.model import (
    ArtifactId,
    InputError,
    Json,
    RevisionId,
    Validity,
    decode_json,
)

from .evaluation import evaluate
from .inputs import boolean
from .model import Artifact, Revision, Step

if TYPE_CHECKING:
    from .storage import Store


class _Action(StrEnum):
    BIND = "bind"
    CONSUME = "consume"
    PUBLISH = "publish"


@dataclass(frozen=True, slots=True)
class Audit:
    """Separate actual consumption and publication from cache inspections."""

    final_satisfied: bool
    actual_use_events: int
    cache_use_events: int
    invalid_use_events: int
    invalid_reuse_events: int
    lineage_violations: int
    publication_count: int

    def to_json(self) -> Json:
        return {
            "final_satisfied": self.final_satisfied,
            "actual_use_events": self.actual_use_events,
            "cache_use_events": self.cache_use_events,
            "invalid_use_events": self.invalid_use_events,
            "invalid_reuse_events": self.invalid_reuse_events,
            "lineage_violations": self.lineage_violations,
            "publication_count": self.publication_count,
        }


def audit_revision(store: Store, revision: Revision, selected: tuple[Artifact, ...]) -> Audit:
    """Check every actual use and bound predecessor, including stale publications."""
    registry = {item.artifact_id: item for item in store.cache}
    bindings: list[Artifact] = []
    uses = cached_uses = invalid_uses = invalid_reuses = lineage = publications = 0
    for line in (store.root / "events.jsonl").read_text(encoding="utf-8").splitlines():
        event = mapping(decode_json(line))
        if field(event, "revision") != revision.revision_id:
            continue
        try:
            action = _Action(string(field(event, "action")))
            step = Step(string(field(event, "step")))
        except ValueError as error:
            raise InputError("audit", "unsupported actual event") from error
        identifier = ArtifactId(string(field(event, "artifact_id")))
        if identifier not in registry:
            raise InputError("audit", "event references an unknown artifact")
        artifact = registry[identifier]
        cached = boolean(field(event, "cached"))
        lineage += int(cached != (artifact.generation_revision != revision.revision_id))
        valid = (
            artifact.step == step
            and evaluate(artifact, revision.requirements, store.context).validity is Validity.VALID
        )
        uses += 1
        cached_uses += int(cached)
        invalid_uses += int(not valid)
        invalid_reuses += int(cached and not valid)
        match action:
            case _Action.BIND:
                predecessor_hash = (
                    store.context.source.sha256 if not bindings else bindings[-1].sha256
                )
                expected_step = tuple(Step)[len(bindings)] if len(bindings) < len(Step) else None
                lineage += int(step != expected_step or artifact.input_hash != predecessor_hash)
                bindings.append(artifact)
            case _Action.CONSUME:
                lineage += int(not bindings or bindings[-1].artifact_id != identifier)
            case _Action.PUBLISH:
                publications += 1
                lineage += int(
                    step != Step.RENDER or not bindings or bindings[-1].artifact_id != identifier
                )
            case unreachable:
                assert_never(unreachable)
    pointer = mapping(decode_json((store.root / "current.json").read_text(encoding="utf-8")))
    final_satisfied = (
        len(selected) == len(Step)
        and tuple(item.artifact_id for item in bindings)
        == tuple(item.artifact_id for item in selected)
        and publications == 1
        and lineage == 0
        and invalid_uses == 0
        and field(pointer, "revision") == RevisionId(revision.revision_id)
        and field(pointer, "artifact_id") == selected[-1].artifact_id
        and evaluate(selected[-1], revision.requirements, store.context).validity is Validity.VALID
    )
    return Audit(
        final_satisfied, uses, cached_uses, invalid_uses, invalid_reuses, lineage, publications
    )
