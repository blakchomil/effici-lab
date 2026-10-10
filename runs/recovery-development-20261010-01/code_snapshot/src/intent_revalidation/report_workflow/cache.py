"""Historical granular cache and executable role contracts share identical permissions."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import assert_never

from src.intent_revalidation.model import Check, Validity, canonical
from src.intent_revalidation.policies import Policy

from .model import Artifact, Revision, Step
from .operations import expected_content, select_rows
from .storage import Exposure, Request, Store, execute


@dataclass(frozen=True, slots=True)
class Result:
    """One revision's actual bindings and operation deltas, excluding evaluation."""

    artifacts: tuple[Artifact, ...]
    counts: dict[str, int]
    durations: dict[str, int]
    started_ns: int
    finished_ns: int


def check_artifact(artifact: Artifact, request: Request, store: Store) -> Check:
    context = store.context
    evidence = (
        artifact.sha256,
        artifact.input_hash,
        artifact.code_hash,
        artifact.env_hash,
        artifact.source_hash,
        artifact.contract_version,
        artifact.generation_revision,
    )
    if not all(evidence):
        return Check(Validity.UNKNOWN, "missing provenance")
    expected = (
        context.code_hash(request.step),
        context.env_hash,
        context.source.sha256,
        context.contract_version,
        store.hash_bytes(request.input_bytes(context)),
    )
    observed = (
        artifact.code_hash,
        artifact.env_hash,
        artifact.source_hash,
        artifact.contract_version,
        artifact.input_hash,
    )
    if observed != expected or artifact.step != request.step:
        return Check(Validity.INVALID, "provenance or input lineage mismatch")
    try:
        content = artifact.path.read_bytes()
    except FileNotFoundError:
        return Check(Validity.UNKNOWN, "artifact bytes missing")
    if store.hash_bytes(content) != artifact.sha256:
        return Check(Validity.INVALID, "byte integrity mismatch")
    if content != expected_content(request.step, request.revision.requirements, context):
        return Check(Validity.INVALID, "role content mismatch")
    return Check(Validity.VALID, "role content and provenance satisfied")


def choose(store: Store, policy: Policy, request: Request) -> Artifact | None:
    expected = store.key(request)
    for artifact in reversed(store.cache):
        if artifact.step != request.step:
            continue
        started = time.perf_counter_ns()
        match policy:
            case Policy.B0:
                return None
            case Policy.B1:
                key_started = time.perf_counter_ns()
                matched = artifact.key == expected
                store.measure("key_comparisons", key_started)
                if not matched:
                    continue
                try:
                    valid = store.hash_bytes(artifact.path.read_bytes()) == artifact.sha256
                except FileNotFoundError:
                    valid = False
                check = Check(
                    Validity.VALID if valid else Validity.INVALID, "granular key and bytes"
                )
                store.measure("integrity_checks", started)
            case Policy.B2:
                check = check_artifact(artifact, request, store)
                store.measure("contract_checks", started)
            case unreachable:
                assert_never(unreachable)
        store.record(
            "assessments.jsonl",
            {
                "revision": request.revision.revision_id,
                "artifact_id": artifact.artifact_id,
                "step": request.step.value,
                "validity": check.validity.value,
                "reason": check.reason,
            },
        )
        if check.validity == Validity.VALID:
            return artifact
    return None


def run_revision(store: Store, policy: Policy, revision: Revision) -> Result:
    started = time.perf_counter_ns()
    previous_counts, previous_durations = store.counts.copy(), store.durations.copy()
    _ = select_rows(revision.requirements, store.context)
    store.measure("preflight", started)
    store.root.mkdir(parents=True, exist_ok=True)
    (store.root / "artifacts").mkdir(exist_ok=True)
    store.record(
        "revisions.jsonl",
        {
            "revision": revision.revision_id,
            "requirements": revision.requirements.to_json(),
            "policy": policy.value,
        },
    )
    initial_ids = {item.artifact_id for item in store.cache}
    selected: list[Artifact] = []
    predecessor = None
    for step in Step:
        request = Request(step, revision, predecessor)
        if predecessor is not None:
            store.expose(
                "consume",
                Exposure(revision, predecessor, predecessor.artifact_id in initial_ids),
            )
        decision_started = time.perf_counter_ns()
        artifact = choose(store, policy, request)
        store.measure("decisions", decision_started)
        if artifact is None:
            artifact = execute(store, request)
        else:
            store.measure("reuse", time.perf_counter_ns())
        store.expose("bind", Exposure(revision, artifact, artifact.artifact_id in initial_ids))
        selected.append(artifact)
        predecessor = artifact
    report = selected[-1]
    store.expose("publish", Exposure(revision, report, report.artifact_id in initial_ids))
    _ = (store.root / "current.json").write_bytes(
        canonical({"revision": revision.revision_id, "artifact_id": report.artifact_id})
    )
    return Result(
        tuple(selected),
        {key: value - previous_counts.get(key, 0) for key, value in store.counts.items()},
        {key: value - previous_durations.get(key, 0) for key, value in store.durations.items()},
        started,
        time.perf_counter_ns(),
    )
