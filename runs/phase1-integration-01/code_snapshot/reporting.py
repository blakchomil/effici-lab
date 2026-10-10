"""Compare observed development outcomes with explicit costs and inference limits."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from .experiment import Outcome


def write_report(root: Path, outcomes: tuple[Outcome, ...]) -> None:
    lines = [
        "# Phase 1: local deterministic comparison", "",
        "Public development cases, one run per case/policy. No AI policy or held-out evaluation.", "",
        "B0 executes all stages. B1 searches all historical granular keys and checks byte integrity. "
        "B2 executes role-specific content checks before reuse. Each starts from the same copied initial cache; "
        "activation cache manifests were compared byte-for-byte.", "",
        "## Observed outcomes", "",
        "| Case | Policy | Final valid | New executions | Reference min | Excess | Reuse links | Semantic checks | Integrity checks | Late executions | Invalid cache use / cache exposures |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for result in outcomes:
        count = result.counters
        executions = count.get("policy_executions", 0)
        lines.append(f"| {result.case_id} | {result.policy.value} | {result.audit.final_satisfied} | {executions} | "
            f"{result.reference.minimum_executions} | {executions - result.reference.minimum_executions} | "
            f"{count.get('reuse_links', 0)} | {count.get('contract_checks', 0)} | "
            f"{count.get('integrity_checks', 0)} | {count.get('late_executions', 0)} | "
            f"{result.audit.invalid_reuse_events} / {result.audit.cache_use_events} |")
    lines.extend(["", "## Actual time (milliseconds)", "",
        "Measured with perf_counter_ns, including history/artifact I/O in the wall windows. "
        "Order B0/B1/B2 is fixed; these tiny single-sample timings are not a speed benchmark.", "",
        "| Case | Policy | Initial compute | Late compute | New compute | Semantic checks | Integrity checks | Binding | First valid result after change | All remaining work quiescent | Policy wall | Evaluator/reference overhead |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"])
    for result in outcomes:
        duration = result.durations_ns
        fields = (result.initial_compute_ns, duration.get("late_executions", 0), duration.get("policy_executions", 0),
            duration.get("contract_checks", 0), duration.get("integrity_checks", 0), duration.get("binding_operations", 0),
            result.time_to_first_valid_ns, result.total_wall_ns, result.policy_wall_ns, result.evaluation_ns)
        values = ["n/a" if value is None else f"{value / 1_000_000:.3f}" for value in fields]
        lines.append(f"| {result.case_id} | {result.policy.value} | " + " | ".join(values) + " |")
    lines.extend(["", "## What was actually selected", ""])
    for result in outcomes:
        path = result.report_path.relative_to(root).as_posix()
        lines.append(f"- {result.case_id}/{result.policy.value}: {', '.join(result.bindings)}. [Actual report]({path})")
    lines.extend(["", "## Cost and validity interpretation", "",
        "The lower bound enumerates all existing-candidate/fresh-stage plans, validates cached content with an independent "
        "source-derived oracle, and checks selected input hashes. It uses one unit per stage execution. "
        "This is a count lower bound for the four allowed operations, not an optimum over elapsed time, "
        "checks, inference, dollars, or arbitrary transformations.", "",
        "Initial computations are performed once per case and cloned, so the repeated initial columns are shared costs, "
        "not additional policy work. D4/D5 perform one real late computation per policy after the change. "
        "Replay preserves start/change/complete order but does not reproduce asynchronous worker cancellation. "
        "No prior CPU duration is invented; no sleep or weighted workload was added.", "",
        "New rendering is counted as computation, including format conversion. Checks, cache comparisons, "
        "decisions and binding costs are measured in metrics.json. Inner key/check timings overlap the decision duration; "
        "they must not be summed twice. Total wall time runs from requirements_changed through work_quiescent. "
        "Independent evaluator/reference overhead occurs afterward and is separately measured. "
        "No model calls, tokens, remote API charges, retries or cancellation occur. Local resource cost in dollars is unestimated.", "",
        "The audit checks every consumption, binding and publication for r1, not just the final pointer. "
        "Cache exposures include repeated use/bind/publication events; each denominator is shown. "
        "Invalid/unknown candidates rejected during B2 inspection are not counted as actual invalid reuse or as a prior reuse proposal. "
        "The implementation emits no reuse proposal before inspection; incorrect reuse proposals are zero in these cases.", "",
        "## Conclusion and limits", "",
        "Inspect the observed table before drawing a conclusion. If B1/B2 reach the count lower bound with valid results, "
        "these development cases leave no demonstrated gap for an AI policy. That is a useful negative finding, "
        "not evidence of AI superiority or general safety. Six synthetic rows, five public structured changes, "
        "a linear graph and trusted generated provenance are the scope. Natural-language interpretation, "
        "unknown contracts, other workflows, parallel failures and unseen changes remain untested.", "",
        "Next research decision: identify one representative real change that these strong baselines cannot already solve "
        "before spending on Phase 2 model evaluation.", "",
    ])
    with (root / "report.md").open("x", encoding="utf-8") as stream:
        _ = stream.write("\n".join(lines))
