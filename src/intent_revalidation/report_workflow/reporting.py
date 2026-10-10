"""Render comparison findings with explicit limits on cost and generalization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.intent_revalidation.policies import Policy

if TYPE_CHECKING:
    from pathlib import Path

    from .cache import Result
    from .outcomes import Outcome


def write_report(root: Path, outcomes: tuple[Outcome, ...], initial: Result) -> None:
    labels = {
        "R1": "Title change",
        "R2": "Column order change",
        "R3": "D4/D5 evidence selection",
        "R4": "Return to original",
    }
    headers = (
        "Change",
        "Policy",
        "Valid final",
        "New report stages",
        "Reference minimum",
        "Cache exposures",
        "Invalid cache uses",
        "Policy ms",
    )
    lines = [
        "# Report workflow follow-up",
        "",
        "Actual input: preserved Phase 1 metrics. Change variants are proposed development cases.",
        "Workflow: select cases -> summarize policy evidence -> render Markdown.",
        "No original experiment, AI policy, hidden benchmark or remote worker was executed.",
        "",
        "| " + " | ".join(headers) + " |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in outcomes:
        values = (
            labels[item.revision.revision_id],
            item.policy.value,
            str(item.audit.final_satisfied),
            str(item.result.counts.get("executions", 0)),
            str(item.reference.minimum_executions),
            str(item.audit.cache_use_events),
            str(item.audit.invalid_reuse_events),
            f"{(item.result.finished_ns - item.result.started_ns) / 1_000_000:.3f}",
        )
        lines.append("| " + " | ".join(values) + " |")
    lines.extend(["", "## Interpretation", ""])
    optimal = all(
        item.result.counts.get("executions", 0) == item.reference.minimum_executions
        and item.audit.final_satisfied
        and item.audit.invalid_use_events == 0
        and item.audit.lineage_violations == 0
        for item in outcomes
        if item.policy is not Policy.B0
    )
    lines.append(
        "Both strong deterministic baselines reached the current-cache execution-count bounds."
        if optimal
        else "A baseline gap or correctness failure was observed; inspect the recorded rows."
    )
    lines.extend(
        [
            "An additional AI policy is not justified by a remaining gap in these cases."
            if optimal
            else "These observations need diagnosis before deciding on AI evaluation.",
            "Phase 2 AI, Phase 3 language evaluation and Phase 4 integration are untested.",
            "",
            "## Accounting and limits",
            "",
            f"Initial stages: {initial.counts.get('executions', 0)}; measured once and cloned.",
            "Original Phase 1 reruns: 0. Reusing measurements does not measure avoided compute.",
            "B2 checks regenerate expected content; this computation is timed.",
            "Workflow hashes: hash_operations + 2 * key_computations.",
            "Setup/evaluator hashes are excluded from the workflow hash counter.",
            "Operation times overlap; adding them would double-count total cost.",
            "One fixed-order stream per policy. Tiny timings cannot establish speed savings.",
            "All inputs are public development cases. Held-out/model isolation is untested.",
            "Unknown/malformed use is unverified. Universal reuse safety is unproven.",
            "This bounded report API has no generic workflow or external adapter.",
            "",
            "Evidence: manifest.json, source_metrics.json, metrics.json, initial/, B0/, B1/, B2/.",
            "Policies preserve revisions, attempts, artifacts, assessments and actual uses.",
            "",
        ]
    )
    with (root / "report.md").open("x", encoding="utf-8") as stream:
        _ = stream.write("\n".join(lines))
