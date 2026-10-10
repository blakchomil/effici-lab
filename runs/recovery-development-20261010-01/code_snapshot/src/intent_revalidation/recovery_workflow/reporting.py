"""Descriptive measured recovery results with explicit scope limits."""

from __future__ import annotations

from statistics import median
from typing import TYPE_CHECKING

from src.intent_revalidation.policies import Policy

if TYPE_CHECKING:
    from pathlib import Path

    from .model import Outcome


def write_report(root: Path, outcomes: tuple[Outcome, ...]) -> None:
    satisfied = sum(item.audit.final_satisfied for item in outcomes)
    lines = [
        "# Bounded recovery comparison",
        "",
        f"Independent current-revision audits satisfied: {satisfied}/{len(outcomes)}.",
        "",
        (
            "Public synthetic between-revision faults over unchanged actual Phase 1 metrics. "
            "Three cyclic policy orders repeat the same six-event trace; these are not independent "
            "user incidents or a process-restart study."
        ),
        "",
        (
            "| Policy | Satisfied | New stages | Invalid reuse / cache exposures | "
            "Median policy wall (ms/event) | Contract checks | Integrity checks | Hashes |"
        ),
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for policy in Policy:
        rows = [item for item in outcomes if item.policy == policy]
        values = (
            policy.value,
            f"{sum(item.audit.final_satisfied for item in rows)}/{len(rows)}",
            str(sum(item.result.counts.get("executions", 0) for item in rows)),
            f"{sum(item.audit.invalid_reuse_events for item in rows)}/"
            + f"{sum(item.audit.cache_use_events for item in rows)}",
            str(median(item.result.finished_ns - item.result.started_ns for item in rows) / 1e6),
            str(sum(item.result.counts.get("contract_checks", 0) for item in rows)),
            str(sum(item.result.counts.get("integrity_checks", 0) for item in rows)),
            str(sum(item.result.counts.get("hash_operations", 0) for item in rows)),
        )
        lines.append("| " + " | ".join(values) + " |")
    lines.extend(
        [
            "",
            (
                "| Repeat | Position | Event | Policy | New stages | Reference | "
                "Fault ms | Prep ms | Policy ms | Evaluation ms | Satisfied |"
            ),
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for item in outcomes:
        values = (
            str(item.repeat),
            str(item.position),
            item.event.event_id,
            item.policy.value,
            str(item.result.counts.get("executions", 0)),
            str(item.reference.minimum_executions),
            f"{item.fault.duration_ns / 1e6:.3f}",
            f"{item.preparation_ns / 1e6:.3f}",
            f"{(item.result.finished_ns - item.result.started_ns) / 1e6:.3f}",
            f"{item.evaluation_ns / 1e6:.3f}",
            str(item.audit.final_satisfied),
        )
        lines.append("| " + " | ".join(values) + " |")
    matches = all(
        item.result.counts.get("executions", 0) == item.reference.minimum_executions
        for item in outcomes
        if item.policy != Policy.B0
    )
    lines.extend(
        [
            "",
            f"B1/B2 matched every measured execution-count reference: {matches}.",
            "",
            (
                "The reference enumerates the pre-policy, post-fault cache after policy completion. "
                "Its bound concerns new stages, not time or dollars. Each revision is audited "
                "immediately, before subsequent damage or pointer changes. Selected byte snapshots "
                "and fault preimages preserve earlier evidence."
            ),
            "",
            (
                "Seed/preparation costs are in shared-costs.json and independent clone costs in "
                "clone-costs.json. Policy wall, fault injection and evaluator overhead are separate; "
                "nested operation durations overlap and must not be summed. Medians are descriptive "
                "local measurements, without a stable speed or total-cost claim."
            ),
            "",
            (
                "No model policy, hidden evaluation, natural-language interpretation, external user "
                "utility, process restart, concurrency or remote recovery was evaluated. Source "
                "experiment reruns, inference calls, tokens and external API charges were zero. "
                "Implementation model costs and local dollar costs were not measured. This trace "
                "does not establish an AI advantage or a need for an AI policy."
            ),
        ]
    )
    with (root / "report.md").open("x", encoding="utf-8") as stream:
        _ = stream.write("\n".join(lines) + "\n")
