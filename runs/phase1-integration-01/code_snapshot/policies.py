"""Comparable policies share the same cache, tools and allowed pipeline operations."""

import time
from enum import StrEnum
from typing import assert_never

from .contracts import check_artifact
from .model import TASKS, Artifact, Check, Revision, Task, Validity, digest
from .pipeline import cache_key
from .storage import Store


class Policy(StrEnum):
    """B0 recomputes; B1 uses granular keys; B2 checks executable role contracts."""

    B0 = "B0"
    B1 = "B1"
    B2 = "B2"


def select_cached(store: Store, policy: Policy, task: Task, revision: Revision,
                  inputs: tuple[Artifact, ...], cache: tuple[Artifact, ...]) -> Artifact | None:
    """Search every historical candidate without using evaluator expectations."""
    expected = cache_key(task, revision.requirements, store.context, inputs)
    for artifact in reversed(cache):
        if artifact.task != task:
            continue
        started = time.perf_counter_ns()
        match policy:
            case Policy.B0:
                return None
            case Policy.B1:
                matches = artifact.cache_key == expected
                store.count("cache_key_comparisons", time.perf_counter_ns() - started)
                if not matches:
                    continue
                started = time.perf_counter_ns()
                try:
                    intact = digest(artifact.path.read_bytes()) == artifact.sha256
                except OSError:
                    intact = False
                check = Check(Validity.VALID if intact else Validity.INVALID,
                              "granular key + actual immutable byte hash" if intact else "cache bytes unavailable or changed")
                store.assess(artifact, revision, "reuse" if intact else "rerun", check,
                             time.perf_counter_ns() - started, "integrity_checks")
            case Policy.B2:
                check = check_artifact(artifact, revision.requirements, store.context, inputs)
                store.assess(artifact, revision, "revalidate", check,
                             time.perf_counter_ns() - started, "contract_checks")
            case unreachable:
                assert_never(unreachable)
        match check.validity:
            case Validity.VALID:
                return artifact
            case Validity.INVALID:
                store.count("rejected_candidates")
            case Validity.UNKNOWN:
                store.count("unknown_assessments")
            case unreachable:
                assert_never(unreachable)
    return None


def run_policy(store: Store, policy: Policy, revision: Revision,
               cache: tuple[Artifact, ...]) -> tuple[Artifact, ...]:
    """Execute real selected work and record every adoption and consumption."""
    selected: list[Artifact] = []
    store.cache_ids = {artifact.id for artifact in cache}
    for task in TASKS:
        inputs = tuple(selected[-1:])
        started = time.perf_counter_ns()
        match policy:
            case Policy.B0:
                cached = None
            case Policy.B1 | Policy.B2:
                cached = select_cached(store, policy, task, revision, inputs, cache)
            case unreachable:
                assert_never(unreachable)
        store.count("policy_decisions", time.perf_counter_ns() - started)
        if cached is None:
            artifact = store.complete(store.start(task, revision, inputs, "policy"))
            action = "rerun"
            _ = store.emit("artifact_constructed", artifact_id=artifact.id, revision_id=revision.id,
                           consumer_role=task.value, action=action)
            if task is Task.RENDER:
                store.count("render_operations")
        else:
            artifact = cached
            action = "reuse"
            store.count("reuse_links")
        store.bind(artifact, revision, action)
        selected.append(artifact)
    return tuple(selected)
