# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Record a stale publication followed by restoration as a separate negative control."""

from __future__ import annotations

import argparse
import platform
import shlex
import sys
from pathlib import Path
from time import perf_counter_ns

from src.intent_revalidation.model import InputError, RevisionId, canonical, digest
from src.intent_revalidation.policies import Policy
from src.intent_revalidation.report_workflow.audit import audit_revision
from src.intent_revalidation.report_workflow.cache import run_revision
from src.intent_revalidation.report_workflow.inputs import load_source
from src.intent_revalidation.report_workflow.model import Column, ReportRequirements, Revision
from src.intent_revalidation.report_workflow.operations import make_context
from src.intent_revalidation.report_workflow.storage import Exposure, Store


class Arguments(argparse.Namespace):
    """Typed paths for the existing project's argparse boundary."""

    metrics: Path = Path("runs/phase1-20261010-01/metrics.json")
    output: Path = Path("runs/audit-negative-control")


def record_control(metrics_path: Path, root: Path, command: str) -> bool:
    """Publish stale bytes, restore the correct pointer, and retain the failed audit."""
    started = perf_counter_ns()
    context = make_context(load_source(metrics_path))
    cases = tuple(sorted({row.case_id for row in context.source.rows}))
    initial = Revision(
        RevisionId("control-S0"), ReportRequirements(cases, "Phase 1 results", tuple(Column))
    )
    changed = Revision(
        RevisionId("control-E1"), ReportRequirements(cases, "Control changed title", tuple(Column))
    )
    root.mkdir(parents=True, exist_ok=False)
    script = Path(__file__).read_bytes()
    with (root / "script_snapshot.py").open("xb") as stream:
        _ = stream.write(script)
    store = Store(root / "workspace", context)
    seed = run_revision(store, Policy.B0, initial)
    result = run_revision(store, Policy.B2, changed)
    before = audit_revision(store, changed, result.artifacts)
    injection_started = perf_counter_ns()
    stale = seed.artifacts[-1]
    store.expose("publish", Exposure(changed, stale, cached=True))
    stale_pointer = canonical({"revision": changed.revision_id, "artifact_id": stale.artifact_id})
    _ = (store.root / "current.json").write_bytes(stale_pointer)
    with (root / "stale-pointer.json").open("xb") as stream:
        _ = stream.write(stale_pointer)
    correct = result.artifacts[-1]
    store.expose("publish", Exposure(changed, correct, cached=False))
    _ = (store.root / "current.json").write_bytes(
        canonical({"revision": changed.revision_id, "artifact_id": correct.artifact_id})
    )
    injection_ns = perf_counter_ns() - injection_started
    evaluation_started = perf_counter_ns()
    after = audit_revision(store, changed, result.artifacts)
    evaluation_ns = perf_counter_ns() - evaluation_started
    detected = (
        before.final_satisfied
        and not after.final_satisfied
        and after.invalid_reuse_events == 1
        and after.lineage_violations == 1
        and after.publication_count == before.publication_count + 2
    )
    with (root / "result.json").open("xb") as stream:
        _ = stream.write(
            canonical(
                {
                    "command": command,
                    "case_origin": "injected development audit negative control",
                    "before_injection": before.to_json(),
                    "after_restoration": after.to_json(),
                    "stale_history_detected": detected,
                    "source_sha256": context.source.sha256,
                    "script_sha256": digest(script),
                    "python": platform.python_version(),
                    "operation_counts": dict(store.counts),
                    "operation_duration_ns": dict(store.durations),
                    "injection_ns": injection_ns,
                    "final_evaluation_ns": evaluation_ns,
                    "control_wall_ns": perf_counter_ns() - started,
                    "timings_overlap": True,
                    "excluded_from_successful_policy_arm_totals": True,
                    "source_experiment_reruns": 0,
                    "inference_calls": 0,
                    "paid_api_cost_usd": 0,
                    "human_time_ns": None,
                    "local_resource_dollar_cost": None,
                }
            )
        )
    return detected


def main() -> int:
    parser = argparse.ArgumentParser(description="Observe stale-publication audit rejection")
    _ = parser.add_argument(
        "--metrics", type=Path, default=Path("runs/phase1-20261010-01/metrics.json")
    )
    _ = parser.add_argument("--output", type=Path, required=True)
    arguments = Arguments()
    _ = parser.parse_args(namespace=arguments)
    command = "PYTHONPATH=. python3 examples/recovery/audit_control.py "
    command += " ".join(shlex.quote(item) for item in sys.argv[1:])
    try:
        detected = record_control(arguments.metrics, arguments.output, command.strip())
    except (InputError, OSError, ValueError, UnicodeError) as error:
        _ = sys.stderr.write(f"Audit control failed: {error}\n")
        return 2
    _ = sys.stdout.write(f"Stale publication detected after restoration: {detected}\n")
    return 0 if detected else 1


if __name__ == "__main__":
    raise SystemExit(main())
