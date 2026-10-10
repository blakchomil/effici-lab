"""Public six-event trace; fault selection never consults the evaluator."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, assert_never

from src.intent_revalidation.fixtures import mapping
from src.intent_revalidation.model import InputError, RevisionId, canonical, digest
from src.intent_revalidation.report_workflow.model import (
    Artifact,
    Column,
    Context,
    ReportRequirements,
    Revision,
    Step,
)
from src.intent_revalidation.report_workflow.storage import Request, Store, cache_key

from .model import Event, Fault, FaultResult, FaultTarget

if TYPE_CHECKING:
    from pathlib import Path


def initial_requirements(context: Context) -> ReportRequirements:
    cases = tuple(sorted({row.case_id for row in context.source.rows}))
    if not {"D1", "D2", "D3", "D4", "D5"} <= set(cases):
        raise InputError("study", "the Phase 1 source must include D1 through D5")
    return ReportRequirements(cases, "Phase 1 results", tuple(Column))


def events(context: Context) -> tuple[Event, ...]:
    original = initial_requirements(context)
    renamed = ReportRequirements(original.case_ids, "Recovery comparison", original.columns)
    return tuple(
        Event(Revision(RevisionId(event_id), requirements), fault)
        for event_id, requirements, fault in (
            ("E1", renamed, Fault.NONE),
            ("E2", renamed, Fault.DELETE_NEWEST_SUMMARY),
            ("E3", renamed, Fault.DELETE_ALL_SUMMARY),
            ("E4", renamed, Fault.CORRUPT_ALL_RENDER),
            ("E5", original, Fault.NONE),
            ("E6", original, Fault.DELETE_NEWEST_SELECT),
        )
    )


def eligible_candidates(store: Store, event: Event) -> tuple[Artifact, ...]:
    """Match existing granular keys using intact historical predecessor bytes."""
    match event.fault:
        case Fault.NONE:
            return ()
        case Fault.DELETE_NEWEST_SELECT:
            target = Step.SELECT
        case Fault.DELETE_NEWEST_SUMMARY | Fault.DELETE_ALL_SUMMARY:
            target = Step.SUMMARY
        case Fault.CORRUPT_ALL_RENDER:
            target = Step.RENDER
        case unreachable:
            assert_never(unreachable)
    predecessor = None
    for step in Step:
        key = cache_key(Request(step, event.revision, predecessor), store.context)
        candidates = tuple(item for item in store.cache if item.step == step and item.key == key)
        if step == target:
            return candidates
        predecessor = next(
            (
                item
                for item in reversed(candidates)
                if item.path.is_file() and digest(item.path.read_bytes()) == item.sha256
            ),
            None,
        )
        if predecessor is None:
            raise InputError("fault", "no intact matching predecessor for the public fault rule")
    raise InputError("fault", "target step was not traversed")


def _damage(artifact: Artifact, archive: Path, fault: Fault) -> FaultTarget:
    if not artifact.path.is_file():
        return FaultTarget(
            str(artifact.artifact_id),
            str(artifact.path),
            None,
            None,
            None,
            "already_missing",
            artifact.sha256,
        )
    before = artifact.path.read_bytes()
    preimage = archive / f"{artifact.artifact_id}.bytes"
    with preimage.open("xb") as stream:
        _ = stream.write(before)
    match fault:
        case Fault.CORRUPT_ALL_RENDER:
            after = before + b"\nInjected between-revision corruption.\n"
            _ = artifact.path.write_bytes(after)
            post_hash, action = digest(after), "corrupt"
        case Fault.DELETE_NEWEST_SELECT | Fault.DELETE_NEWEST_SUMMARY | Fault.DELETE_ALL_SUMMARY:
            artifact.path.unlink()
            post_hash, action = None, "delete"
        case Fault.NONE:
            raise InputError("fault", "no-fault event cannot damage an artifact")
        case unreachable:
            assert_never(unreachable)
    return FaultTarget(
        str(artifact.artifact_id),
        str(artifact.path),
        str(preimage),
        digest(before),
        post_hash,
        action,
        artifact.sha256,
    )


def inject_fault(store: Store, event: Event) -> FaultResult:
    started = time.perf_counter_ns()
    directory = store.root / "events" / event.event_id
    archive = directory / "fault-archive"
    archive.mkdir(parents=True, exist_ok=False)
    eligible = eligible_candidates(store, event)
    match event.fault:
        case Fault.NONE:
            selected = ()
        case Fault.DELETE_NEWEST_SELECT | Fault.DELETE_NEWEST_SUMMARY:
            if not eligible[:-1]:
                raise InputError("fault", "newest-only fault requires an older matching candidate")
            selected = eligible[-1:]
        case Fault.DELETE_ALL_SUMMARY | Fault.CORRUPT_ALL_RENDER:
            if not eligible:
                raise InputError("fault", "all-candidate fault has no eligible candidate")
            selected = eligible
        case unreachable:
            assert_never(unreachable)
    targets = tuple(_damage(item, archive, event.fault) for item in selected)
    result = FaultResult(
        targets, time.perf_counter_ns() - started, tuple(str(item.artifact_id) for item in eligible)
    )
    with (directory / "fault.json").open("xb") as stream:
        _ = stream.write(
            canonical(
                {"event": event.event_id, "rule": event.fault.value, **mapping(result.to_json())}
            )
        )
    return result
