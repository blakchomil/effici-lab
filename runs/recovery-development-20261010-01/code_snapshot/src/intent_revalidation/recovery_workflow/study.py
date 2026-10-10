"""Execute the public bounded fault trace through unchanged report policies."""

from __future__ import annotations

import time
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from src.intent_revalidation.model import InputError, Json, RevisionId
from src.intent_revalidation.policies import Policy
from src.intent_revalidation.report_workflow.audit import audit_revision
from src.intent_revalidation.report_workflow.cache import run_revision
from src.intent_revalidation.report_workflow.inputs import load_source
from src.intent_revalidation.report_workflow.model import Revision
from src.intent_revalidation.report_workflow.operations import make_context
from src.intent_revalidation.report_workflow.reference import enumerate_plans
from src.intent_revalidation.report_workflow.storage import Store
from src.intent_revalidation.report_workflow.study import fingerprint

from .model import Event, Outcome
from .recording import snapshot_cache, snapshot_result, write_json, write_manifest
from .reporting import write_report
from .scenarios import events, initial_requirements, inject_fault

if TYPE_CHECKING:
    from src.intent_revalidation.report_workflow.cache import Result


def _cost(result: Result) -> Json:
    return {
        "operation_counts": dict(result.counts),
        "operation_duration_ns": dict(result.durations),
        "wall_ns": result.finished_ns - result.started_ns,
    }


def _run_event(store: Store, policy: Policy, event: Event) -> Outcome:
    preparation_started = time.perf_counter_ns()
    directory = store.root / "events" / event.event_id
    directory.mkdir(parents=True)
    snapshot_cache(directory / "activation-cache.json", store.cache)
    preparation_ns = time.perf_counter_ns() - preparation_started
    fault = inject_fault(store, event)
    started = time.perf_counter_ns()
    cache = store.cache
    snapshot_cache(directory / "availability.json", cache)
    preparation_ns += time.perf_counter_ns() - started
    result = run_revision(store, policy, event.revision)
    started = time.perf_counter_ns()
    audit = audit_revision(store, event.revision, result.artifacts)
    reference = enumerate_plans(cache, event.revision.requirements, store.context)
    evaluation_ns = time.perf_counter_ns() - started
    snapshot_result(directory / "selected-artifacts", result)
    return Outcome(
        event.revision,
        policy,
        result,
        audit,
        reference,
        evaluation_ns,
        0,
        0,
        event,
        fault,
        preparation_ns,
    )


def _execute(root: Path, seed: Store, trace: tuple[Event, ...]) -> tuple[Outcome, ...]:
    outcomes: list[Outcome] = []
    clones: list[Json] = []
    policies = tuple(Policy)
    for offset in range(len(policies)):
        order = policies[offset:] + policies[:offset]
        for position, policy in enumerate(order, 1):
            started = time.perf_counter_ns()
            store = seed.clone(root / f"repeat-{offset + 1}" / policy.value)
            if fingerprint(store) != fingerprint(seed):
                raise InputError("clone", "common seed fingerprint differs")
            clones.append(
                {
                    "repeat": offset + 1,
                    "policy": policy.value,
                    "duration_ns": time.perf_counter_ns() - started,
                }
            )
            snapshot_cache(store.root / "initial-cache.json", store.cache)
            for event in trace:
                outcome = replace(
                    _run_event(store, policy, event), repeat=offset + 1, position=position
                )
                outcomes.append(outcome)
                store.record("outcomes.jsonl", outcome.to_json())
                store.record("audit_assessments.jsonl", outcome.audit.to_json())
                write_json(
                    store.root / "events" / event.event_id / "outcome.json", outcome.to_json()
                )
    write_json(root / "clone-costs.json", clones)
    return tuple(outcomes)


def _require_seed(*, satisfied: bool) -> None:
    if not satisfied:
        raise InputError("seed", "initial report failed independent audit")


def run_study(metrics_path: Path, root: Path, command: str) -> tuple[Outcome, ...]:
    started = time.perf_counter_ns()
    source = load_source(metrics_path)
    context = make_context(source)
    initial = initial_requirements(context)
    trace = events(context)
    protocol = (
        Path(__file__).resolve().parents[3] / "examples/recovery/protocol-20261010.md"
    ).read_bytes()
    root.mkdir(parents=True, exist_ok=False)
    try:
        with (root / "source_metrics.json").open("xb") as stream:
            _ = stream.write(source.content)
        with (root / "protocol.md").open("xb") as stream:
            _ = stream.write(protocol)
        write_manifest(root, context, command)
        preparation_ns = time.perf_counter_ns() - started
        seed = Store(root / "seed", context)
        seed_costs: list[Json] = []
        for revision_id in ("S0", "S1"):
            revision = Revision(RevisionId(revision_id), initial)
            result = run_revision(seed, Policy.B0, revision)
            evaluation_started = time.perf_counter_ns()
            audit = audit_revision(seed, revision, result.artifacts)
            evaluation_ns = time.perf_counter_ns() - evaluation_started
            seed_costs.append(
                {
                    "revision": revision_id,
                    "cost": _cost(result),
                    "audit": audit.to_json(),
                    "evaluation_ns": evaluation_ns,
                }
            )
            _require_seed(satisfied=audit.final_satisfied)
        write_json(
            root / "shared-costs.json",
            {
                "preparation_ns": preparation_ns,
                "seed_runs": seed_costs,
                "seed_operation_counts": dict(seed.counts),
                "seed_operation_duration_ns": dict(seed.durations),
                "clone_costs_path": "clone-costs.json",
                "timing_note": "internal operation durations overlap; do not sum them",
            },
        )
        outcomes = _execute(root, seed, trace)
        write_json(root / "metrics.json", [item.to_json() for item in outcomes])
        write_report(root, outcomes)
    except (InputError, OSError, ValueError, UnicodeError) as error:
        write_json(root / "failure.json", {"error": str(error), "type": type(error).__name__})
        raise
    return outcomes
