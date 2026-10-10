"""Compare observed development outcomes with explicit costs and inference limits."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .policies import Policy

if TYPE_CHECKING:
    from pathlib import Path

    from .experiment import Outcome


def paragraph(*chunks: str) -> str:
    return " ".join(chunks)


def table_row(*cells: str) -> str:
    return "| " + " | ".join(cells) + " |"


def write_report(root: Path, outcomes: tuple[Outcome, ...]) -> None:
    lines = [
        "# Phase 1: local deterministic comparison",
        "",
        "Public development cases, one run per case/policy. No AI or held-out evaluation.",
        "",
        paragraph(
            "B0 executes every stage. B1 searches all historical granular keys and checks",
            "byte hashes.",
            "B2 checks executable role contracts before reuse. Each starts from the same",
            "copied cache.",
            "Activation cache manifests were compared byte-for-byte across all three policies.",
        ),
        "",
        "## Observed outcomes",
        "",
        table_row(
            "Case",
            "Policy",
            "Final valid",
            "New executions",
            "Reference min",
            "Excess",
            "Reuse links",
            "Semantic checks",
            "Integrity checks",
            "Late executions",
            "Invalid cache use / cache exposures",
        ),
        table_row("---", "---", "---", *(["---:"] * 7), "---"),
    ]
    for result in outcomes:
        count = result.counters
        executions = count.get("policy_executions", 0)
        lines.append(
            table_row(
                result.case_id,
                result.policy.value,
                str(result.audit.final_satisfied),
                str(executions),
                str(result.reference.minimum_executions),
                str(executions - result.reference.minimum_executions),
                str(count.get("reuse_links", 0)),
                str(count.get("contract_checks", 0)),
                str(count.get("integrity_checks", 0)),
                str(count.get("late_executions", 0)),
                f"{result.audit.invalid_reuse_events} / {result.audit.cache_use_events}",
            )
        )
    lines.extend(
        [
            "",
            "## Actual time (milliseconds)",
            "",
            paragraph(
                "Measured with perf_counter_ns. Wall windows include history and artifact I/O.",
                "Order B0/B1/B2 is fixed. These tiny single-sample timings are not a speed",
                "benchmark.",
            ),
            "",
            table_row(
                "Case",
                "Policy",
                "Initial compute",
                "Late compute",
                "New compute",
                "Semantic checks",
                "Integrity checks",
                "Binding",
                "First valid after change",
                "All remaining work quiescent",
                "Policy wall",
                "Evaluator/reference overhead",
            ),
            table_row("---", "---", *(["---:"] * 10)),
        ]
    )
    for result in outcomes:
        duration = result.durations_ns
        fields = (
            result.initial_compute_ns,
            duration.get("late_executions", 0),
            duration.get("policy_executions", 0),
            duration.get("contract_checks", 0),
            duration.get("integrity_checks", 0),
            duration.get("binding_operations", 0),
            result.time_to_first_valid_ns,
            result.total_wall_ns,
            result.policy_wall_ns,
            result.evaluation_ns,
        )
        values = ["n/a" if value is None else f"{value / 1_000_000:.3f}" for value in fields]
        lines.append(table_row(result.case_id, result.policy.value, *values))
    lines.extend(["", "## Actual selections", ""])
    for result in outcomes:
        path = result.report_path.relative_to(root).as_posix()
        label = f"{result.case_id}/{result.policy.value}: {', '.join(result.bindings)}."
        lines.append(f"- {label} [Actual report]({path})")
    lines.extend(
        [
            "",
            "## Cost and validity interpretation",
            "",
            paragraph(
                "The reference enumerates every existing-candidate/fresh-stage combination in",
                "the current cache.",
                "An independent CSV oracle checks candidate content and selected input hashes.",
                "Each execution costs one declared unit. This is a lower bound on the",
                "four-stage execution count.",
                "It is not an optimum over elapsed time, validation, inference, dollars or",
                "arbitrary transforms.",
            ),
            "",
            paragraph(
                "Initial computation runs once per case and is cloned; repeated initial columns",
                "are shared costs.",
                "D4/D5 execute one real late computation per policy after the requirement change.",
                "Replay preserves start/change/complete order but does not reproduce parallel",
                "cancellation.",
                "No historical CPU duration, artificial sleep or weighted workload was added.",
            ),
            "",
            paragraph(
                "New rendering, including format conversion, is counted as computation.",
                "Checks, key comparisons, decisions and bindings have counts and durations in",
                "metrics.json.",
                "Inner key/check time overlaps decision time and must not be added twice.",
                "Total wall time runs from requirements_changed through work_quiescent.",
                "Evaluator/reference overhead occurs afterward and is measured separately.",
                "There are no model calls, tokens, API charges, retries or cancellations.",
                "Local resource dollar cost is unestimated.",
            ),
            "",
            paragraph(
                "The audit checks every actual consumption, binding and publication under the",
                "target revision.",
                "Cache exposures count use/bind/publication events, including repeated exposure",
                "of one artifact.",
                "Rejected invalid/unknown candidates are distinct from actual invalid reuse.",
                "These policies emit no reuse proposal before inspection, so incorrect reuse",
                "proposals are zero.",
            ),
            "",
            "## Conclusion and limits",
            "",
        ]
    )
    for policy in Policy:
        results = tuple(item for item in outcomes if item.policy is policy)
        executions = sum(item.counters.get("policy_executions", 0) for item in results)
        valid = sum(item.audit.final_satisfied for item in results)
        lines.append(
            f"- {policy.value}: {valid}/{len(results)} valid; {executions} new executions."
        )
    optimal = all(
        item.audit.final_satisfied
        and item.counters.get("policy_executions", 0) == item.reference.minimum_executions
        for item in outcomes
        if item.policy is not Policy.B0
    )
    lines.extend(
        [
            "",
            paragraph(
                "Both strong baselines reach the execution-count lower bound with valid outputs."
                if optimal
                else "Some strong baseline results miss validity or the execution-count bound.",
                "No added value of AI is established by this experiment.",
                "Scope: six synthetic rows, five public structured changes, linear graph and",
                "generated provenance.",
                "Unseen changes, natural-language interpretation, other workflows and parallel",
                "failures are untested.",
                "Zero observed invalid reuse is a finite development result, not a proof of",
                "general safety.",
            ),
            "",
            paragraph(
                "Next research decision: find one representative real requirement change that",
                "strong baselines",
                "cannot already solve before spending on Phase 2 model evaluation.",
            ),
            "",
        ]
    )
    with (root / "report.md").open("x", encoding="utf-8") as stream:
        _ = stream.write("\n".join(lines))
