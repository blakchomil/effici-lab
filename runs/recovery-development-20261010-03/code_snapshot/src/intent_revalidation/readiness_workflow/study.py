"""Run a fixed public observed case with equal information and independent caches."""

from __future__ import annotations

from time import perf_counter_ns
from typing import TYPE_CHECKING, Final

from src.intent_revalidation.fixtures import mapping
from src.intent_revalidation.model import InputError, Json, RevisionId, decode_json
from src.intent_revalidation.policies import Policy
from src.intent_revalidation.report_workflow.cache import run_revision
from src.intent_revalidation.report_workflow.inputs import load_source
from src.intent_revalidation.report_workflow.model import Column, ReportRequirements, Revision
from src.intent_revalidation.report_workflow.operations import make_context
from src.intent_revalidation.report_workflow.storage import Store
from src.intent_revalidation.report_workflow.study import fingerprint

from .audit import audit_arm
from .execution import Arm, ArmRun, CaseInputs, execute_arm
from .inputs import parse_clarification, parse_snapshot
from .interpretation import interpret
from .model import Control, Meaning
from .recording import preserve_inputs, write_json, write_report

if TYPE_CHECKING:
    from pathlib import Path

REPETITIONS: Final = 5


def run_study(metrics: Path, case: Path, root: Path) -> tuple[Json, ...]:
    """Validate input and meaning before creating an immutable run directory."""
    preparation_started = perf_counter_ns()
    source = load_source(metrics)
    context = make_context(source)
    snapshot = parse_snapshot((case / "current-facts-20261010.json").read_bytes())
    clarification = parse_clarification((case / "clarification-20261010.json").read_bytes())
    for control in Control:
        if interpret(clarification, control).meaning != Meaning.READINESS:
            raise InputError("clarification", "readiness meaning remains unresolved or unsupported")
    previous = (case / "runs/observed-02/retitled-report.md").read_bytes()
    requirements = ReportRequirements(
        tuple(sorted({row.case_id for row in source.rows})), "Support readiness", tuple(Column)
    )
    inputs = CaseInputs(
        snapshot, clarification, requirements, (case / "request.md").read_bytes(), previous
    )
    root.mkdir(parents=True, exist_ok=False)
    preserve_inputs(root, case, metrics)
    preparation_ns = perf_counter_ns() - preparation_started
    seed = Store(root / "initial", context)
    initial = run_revision(seed, Policy.B0, Revision(RevisionId("numeric-R0"), requirements))
    if initial.artifacts[-1].path.read_bytes() != previous:
        raise InputError(
            "previous_report", "common replay seed differs from actual prior numeric report"
        )
    write_json(
        root / "shared-costs.json",
        {
            "input_preparation_ns": preparation_ns,
            "seed_counts": dict(initial.counts),
            "seed_duration_ns": dict(initial.durations),
            "seed_wall_ns": initial.finished_ns - initial.started_ns,
            "scope": "new measured replay seed, byte-equal to prior report; not imported old cache",
        },
    )
    arms = (
        Arm(None, Policy.B0),
        *(Arm(control, policy) for control in Control for policy in (Policy.B1, Policy.B2)),
    )
    cache_fingerprint = fingerprint(seed)
    runs: list[tuple[int, int, int, ArmRun]] = []
    for repetition in range(REPETITIONS):
        order = arms[repetition:] + arms[:repetition]
        for position, arm in enumerate(order):
            clone_started = perf_counter_ns()
            store = seed.clone(root / f"repeat-{repetition + 1}" / arm.name)
            clone_ns = perf_counter_ns() - clone_started
            if fingerprint(store) != cache_fingerprint:
                raise InputError("cache", "initial arm cache differs from shared seed")
            write_json(
                store.root / "activation-cache.json", decode_json(cache_fingerprint.decode())
            )
            run = execute_arm(store, arm, inputs)
            runs.append((repetition + 1, position + 1, clone_ns, run))
    outcomes: list[Json] = []
    for repetition, position, clone_ns, run in runs:
        assessed = mapping(audit_arm(run, inputs))
        row: Json = {
            **assessed,
            "repetition": repetition,
            "order_position": position,
            "clone_ns": clone_ns,
        }
        outcomes.append(row)
        write_json(run.store.root / "outcome.json", row)
    result = tuple(outcomes)
    write_json(root / "metrics.json", list(result))
    write_report(root, result)
    return result
