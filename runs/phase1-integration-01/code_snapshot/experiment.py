"""Run isolated baseline comparisons; evaluator results never enter policy selection."""

from __future__ import annotations

import platform
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .audit import Audit, audit_history, cache_fingerprint
from .evaluation import evaluate
from .fixtures import load_suite
from .model import Context, Json, Validity, canonical, digest
from .policies import Policy, run_policy
from .reference import ReferenceResult, enumerate_plans
from .replay import prepare_initial, replay
from .storage import Store

if TYPE_CHECKING:
    from .fixtures import Case, Suite


@dataclass(frozen=True, slots=True)
class Outcome:
    """Observed costs keep execution counts, operation timings and wall time separate."""

    case_id: str
    policy: Policy
    audit: Audit
    reference: ReferenceResult
    counters: dict[str, int]
    durations_ns: dict[str, int]
    initial_executions: int
    initial_compute_ns: int
    time_to_first_valid_ns: int | None
    total_wall_ns: int
    policy_wall_ns: int
    evaluation_ns: int
    unnecessary_executions: int
    bindings: tuple[str, ...]
    report_path: Path

    def to_json(self) -> Json:
        return {
            "case_id": self.case_id, "policy": self.policy.value,
            "audit": self.audit.to_json(), "reference": self.reference.to_json(),
            "operation_counts": dict(self.counters), "operation_duration_ns": dict(self.durations_ns),
            "initial_executions": self.initial_executions, "initial_compute_ns": self.initial_compute_ns,
            "time_to_first_valid_ns": self.time_to_first_valid_ns,
            "requirement_change_to_quiescence_ns": self.total_wall_ns,
            "policy_activation_to_quiescence_ns": self.policy_wall_ns,
            "evaluation_and_reference_ns": self.evaluation_ns,
            "unnecessary_executions": self.unnecessary_executions,
            "excess_executions_over_reference": self.counters.get("policy_executions", 0) - self.reference.minimum_executions,
            "bindings": list(self.bindings), "report_path": str(self.report_path),
            "inference_calls": 0, "tokens": 0, "external_api_cost_usd": 0,
            "local_resource_dollar_cost": None,
            "incorrect_reuse_proposals": 0, "remaining_attempts": 0,
            "cancellation_requests": 0, "completed_cancellations": 0,
            "timing_scope": "measured synchronous local replay; no historical or parallel timing inferred",
        }


def run_one(seed: Store, case: Case, suite: Suite, policy: Policy) -> Outcome:
    store = seed.clone(seed.root.parent / policy.value)
    changed_ns = replay(store, case, suite.initial)
    cache = tuple(store.artifacts)
    with (store.root / "activation_cache.json").open("xb") as stream:
        _ = stream.write(canonical(cache_fingerprint(cache)))
    activation_ns = store.emit("policy_activated", revision_id=case.target.id, policy=policy.value,
                               available_artifact_ids=[item.id for item in cache])
    selected = run_policy(store, policy, case.target, cache)
    _ = store.publish(selected, case.target)
    completed_ns = store.emit("work_quiescent", revision_id=case.target.id, active_attempts=len(store.active))
    if store.active:
        message = "experiment left an unfinished attempt"
        raise RuntimeError(message)
    audit_start = time.perf_counter_ns()
    audit = audit_history(store, case.target)
    reference = enumerate_plans(cache, case.target.requirements, store.context)
    valid_cached_tasks = {
        item.task for item in cache
        if evaluate(item, case.target.requirements, store.context).validity is Validity.VALID
    }
    unnecessary = sum(item.task in valid_cached_tasks for item in selected if item.id not in store.cache_ids)
    bindings = tuple(f"{item.task.value}:{'reuse' if item.id in store.cache_ids else 'rerun'}" for item in selected)
    first_valid = None if audit.first_valid_ns is None else audit.first_valid_ns - changed_ns
    outcome = Outcome(case.id, policy, audit, reference, dict(store.counters), dict(store.durations_ns),
        seed.counters.get("initial_executions", 0), seed.durations_ns.get("initial_executions", 0),
        first_valid, completed_ns - changed_ns, completed_ns - activation_ns,
        time.perf_counter_ns() - audit_start, unnecessary, bindings, selected[-1].path)
    with (store.root / "metrics.json").open("xb") as stream:
        _ = stream.write(canonical(outcome.to_json()))
    return outcome


def run_experiment(cases_path: Path, root: Path, command: str) -> tuple[Outcome, ...]:
    suite = load_suite(cases_path)
    source = suite.source_path.read_bytes()
    environment: Json = {"python": sys.version, "implementation": platform.python_implementation(),
                         "system": platform.system(), "release": platform.release(), "machine": platform.machine()}
    code_files = sorted(Path(__file__).parent.glob("*.py"))
    hashes: dict[str, Json] = {path.name: digest(path.read_bytes()) for path in code_files}
    context = Context(suite.dataset_id, source, digest(source), digest(canonical(hashes)), digest(canonical(environment)))
    root.mkdir(parents=True, exist_ok=False)
    (root / "code_snapshot").mkdir()
    for path in code_files:
        with (root / "code_snapshot" / path.name).open("xb") as stream:
            _ = stream.write(path.read_bytes())
    with (root / "source.csv").open("xb") as stream:
        _ = stream.write(source)
    with (root / "dev_cases.json").open("xb") as stream:
        _ = stream.write(cases_path.read_bytes())
    manifest: Json = {
        "phase": 1, "visibility": "public_development_only", "command": command,
        "dataset_id": context.dataset_id, "source_sha256": context.source_sha256,
        "code_sha256": context.code_sha256, "code_files": hashes, "environment": environment,
        "environment_sha256": context.environment_sha256, "contract_version": context.contract_version,
        "code_identity": "actual source-file manifest; repository has no commit yet",
        "tasks": [{"id": task.value, "consumer_role": role, "direct_requirement_fields": fields}
                  for task, role, fields in (
                      (suite.cases[0].completed_tasks[0], "raw_records", ["dataset_id"]),
                  )],
        "cost_model": {"execution_count_weight_per_stage": 1, "hardware_time_is_not_optimized": True,
            "timings_overlap": "policy_decisions include inner check/key timings; do not add them twice",
            "evaluation_overhead_is_separate": True, "no_sleep": True},
        "initial_cache": "one actual seed execution per case, copied into each isolated policy workspace",
        "policy_order": [policy.value for policy in Policy], "repetitions": 1,
        "held_out": False, "model_policy_evaluated": False, "process_isolation": False,
    }
    with (root / "manifest.json").open("xb") as stream:
        _ = stream.write(canonical(manifest))
    outcomes: list[Outcome] = []
    for case in suite.cases:
        seed = Store(root / case.id / "initial", context)
        prepare_initial(seed, case, suite.initial)
        case_outcomes = tuple(run_one(seed, case, suite, policy) for policy in Policy)
        fingerprints = [(root / case.id / policy.value / "activation_cache.json").read_bytes() for policy in Policy]
        if len(set(fingerprints)) != 1:
            message = f"initial cache fairness failed for {case.id}"
            raise RuntimeError(message)
        outcomes.extend(case_outcomes)
    with (root / "metrics.json").open("xb") as stream:
        _ = stream.write(canonical([outcome.to_json() for outcome in outcomes]))
    return tuple(outcomes)
