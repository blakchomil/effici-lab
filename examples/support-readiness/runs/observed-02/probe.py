#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
# How to run (from the repository root):
# Install uv if needed: curl -LsSf https://astral.sh/uv/install.sh | sh
# PYTHONPATH=. uv run examples/support-readiness/probe.py OUTPUT_DIRECTORY
"""Probe the existing report interface against an explicitly agent-derived target."""

from __future__ import annotations

import sys
from dataclasses import fields
from pathlib import Path
from time import perf_counter_ns
from typing import Final

from src.intent_revalidation.model import InputError, Json, RevisionId, canonical, digest
from src.intent_revalidation.policies import Policy
from src.intent_revalidation.report_workflow.audit import audit_revision
from src.intent_revalidation.report_workflow.cache import run_revision
from src.intent_revalidation.report_workflow.inputs import load_source
from src.intent_revalidation.report_workflow.model import Column, ReportRequirements, Revision
from src.intent_revalidation.report_workflow.operations import make_context
from src.intent_revalidation.report_workflow.storage import Store

EXPECTED_REUSED_STAGES: Final = 2


def probe(output: Path) -> bool:
    """Write immutable evidence; a second invocation with the same directory fails."""
    started = perf_counter_ns()
    case = Path(__file__).resolve().parent
    repository = case.parent.parent
    source = load_source(repository / "runs/phase1-20261010-01/metrics.json")
    context = make_context(source)
    output.mkdir(parents=True, exist_ok=False)
    inputs = (case / "request.md", case / "repository-snapshot.json", Path(__file__))
    for path in inputs:
        _ = (output / path.name).write_bytes(path.read_bytes())
    _ = (output / "source_metrics.json").write_bytes(source.content)
    store = Store(output / "workflow", context)
    cases = tuple(sorted({row.case_id for row in source.rows}))
    initial = Revision(RevisionId("initial"), ReportRequirements(cases, "Results", tuple(Column)))
    seed = run_revision(store, Policy.B0, initial)
    changed = Revision(
        RevisionId("readiness-title"),
        ReportRequirements(cases, "Support readiness", tuple(Column)),
    )
    result = run_revision(store, Policy.B1, changed)
    audit = audit_revision(store, changed, result.artifacts)
    rejected: list[Json] = []
    accepted: list[Json] = []
    for name in ("license", "maintenance_evidence", "ai_credit_need"):
        try:
            column = Column(name)
        except ValueError as error:
            rejected.append({"field": name, "error": str(error)})
        else:
            accepted.append(column.value)
    _ = (output / "retitled-report.md").write_bytes(result.artifacts[-1].path.read_bytes())
    observed = (
        audit.final_satisfied
        and result.counts.get("executions", 0) == 1
        and result.counts.get("reuse", 0) == EXPECTED_REUSED_STAGES
        and not accepted
    )
    checks: Json = {
        "scenario": "Observed critique with an agent-derived support-readiness report target",
        "invocation": "PYTHONPATH=. uv run examples/support-readiness/probe.py OUTPUT_DIRECTORY",
        "argv": list(sys.argv),
        "probe_observations_match": observed,
        "source_sha256": source.sha256,
        "input_hashes": {path.name: digest(path.read_bytes()) for path in inputs},
        "source_file_hashes": {
            str(path.relative_to(repository)): digest(path.read_bytes())
            for path in sorted((repository / "src").rglob("*.py"))
        },
        "requirements_fields": [item.name for item in fields(ReportRequirements)],
        "supported_columns": [item.value for item in Column],
        "rejected_readiness_columns": rejected,
        "accepted_readiness_columns": accepted,
        "initial_generation_counts": dict(seed.counts),
        "title_change_counts": dict(result.counts),
        "title_change_durations_ns": dict(result.durations),
        "title_change_wall_ns": result.finished_ns - result.started_ns,
        "audit": audit.to_json(),
        "original_experiment_reruns": 0,
        "evaluated_model_calls": 0,
        "evaluated_model_tokens": 0,
        "external_api_cost_usd": 0,
        "local_cost_usd": None,
        "ai_implementation_session_cost": "not measured; excluded from runtime probe",
        "probe_wall_ns_before_final_write": perf_counter_ns() - started,
        "finding": "Current report interface lacks readiness fields and repository-fact inputs",
        "strong_deterministic_baseline_failure": False,
        "ai_advantage_demonstrated": False,
    }
    _ = (output / "result.json").write_bytes(canonical(checks))
    return observed


def main() -> int:
    """Require an explicit new output directory and expose the probe's exit status."""
    arguments = sys.argv[1:]
    if len(arguments) != 1:
        raise InputError("output", "expected exactly one new output directory")
    return 0 if probe(Path(arguments[0])) else 1


if __name__ == "__main__":
    raise SystemExit(main())
