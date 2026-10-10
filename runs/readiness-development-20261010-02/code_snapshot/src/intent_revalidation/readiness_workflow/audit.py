"""Audit numeric reuse and the final composition's recorded actual exposures."""

from __future__ import annotations

from time import perf_counter_ns
from typing import TYPE_CHECKING

from src.intent_revalidation.fixtures import field, mapping
from src.intent_revalidation.model import Json, JsonObject, Validity, decode_json, digest
from src.intent_revalidation.report_workflow.audit import audit_revision
from src.intent_revalidation.report_workflow.inputs import boolean
from src.intent_revalidation.report_workflow.reference import enumerate_plans

from .evaluation import NumericContract, audit_document
from .model import Meaning

if TYPE_CHECKING:
    from .execution import ArmRun, CaseInputs


def audit_arm(run: ArmRun, inputs: CaseInputs) -> Json:
    """Use frozen confirmed expectations rather than the policy's selected meaning."""
    started = perf_counter_ns()
    numeric_audit = audit_revision(run.store, run.revision, run.numeric.artifacts)
    final = run.document.read_bytes()
    check = audit_document(
        final, inputs.snapshot, NumericContract(inputs.requirements, run.store.context)
    )
    report = run.numeric.artifacts[-1]
    numeric_bytes = report.path.read_bytes()
    cached_report = report.generation_revision != run.revision.revision_id
    expected_events: list[JsonObject] = [
        {
            "action": "consume",
            "role": "numeric_report",
            "artifact_id": report.artifact_id,
            "actual_sha256": digest(numeric_bytes),
            "expected_sha256": report.sha256,
            "cached": cached_report,
        },
        {
            "action": "consume",
            "role": "repository_facts",
            "actual_sha256": inputs.snapshot.sha256,
            "expected_sha256": inputs.snapshot.sha256,
            "cached": False,
        },
        {
            "action": "publish",
            "role": "readiness_report",
            "actual_sha256": digest(final),
            "expected_sha256": digest(final),
            "cached": False,
        },
    ]
    observed = [
        decode_json(line)
        for line in (run.store.root / "readiness-events.jsonl").read_text().splitlines()
    ]
    lineage = int(observed != expected_events)
    pointer = mapping(decode_json((run.store.root / "current-readiness.json").read_text()))
    lineage += int(
        field(pointer, "path") != run.document.name or field(pointer, "sha256") != digest(final)
    )
    preserved = numeric_bytes == inputs.previous_report
    expected_by_role = {
        "numeric_report": expected_events[0],
        "repository_facts": expected_events[1],
        "readiness_report": expected_events[2],
    }
    valid_roles = {
        "numeric_report": numeric_audit.final_satisfied and preserved,
        "repository_facts": True,
        "readiness_report": check.validity == Validity.VALID,
    }
    invalid_composition_reuse = invalid_composition_uses = cached_exposures = 0
    for value in observed:
        event = mapping(value)
        role = field(event, "role")
        expected = expected_by_role.get(str(role))
        valid = event == expected and valid_roles.get(str(role), False)
        cached = boolean(field(event, "cached"))
        invalid_composition_uses += int(not valid)
        cached_exposures += int(cached)
        invalid_composition_reuse += int(cached and not valid)
    invalid_reuse = numeric_audit.invalid_reuse_events + invalid_composition_reuse
    initial_cache = tuple(
        item for item in run.store.cache if item.generation_revision != run.revision.revision_id
    )
    reference = enumerate_plans(initial_cache, inputs.requirements, run.store.context)
    execution_count = run.numeric.counts.get("executions", 0) + 1
    interpretation_error = run.interpretation.meaning != Meaning.READINESS
    satisfied = (
        numeric_audit.final_satisfied
        and check.validity == Validity.VALID
        and preserved
        and not lineage
        and not invalid_reuse
        and not invalid_composition_uses
        and not interpretation_error
    )
    return {
        "arm": run.arm.name,
        "final_satisfied": satisfied,
        "interpretation": run.interpretation.to_json(),
        "interpretation_error": interpretation_error,
        "capability_unsupported": False,
        "document_check": check.to_json(),
        "numeric_audit": numeric_audit.to_json(),
        "numeric_bytes_preserved": preserved,
        "composition_lineage_violations": lineage,
        "invalid_composition_use_events": invalid_composition_uses,
        "invalid_reuse_events": invalid_reuse,
        "cache_exposure_events": numeric_audit.cache_use_events + cached_exposures,
        "numeric_stage_executions": run.numeric.counts.get("executions", 0),
        "composition_executions": 1,
        "total_stage_executions": execution_count,
        "numeric_stage_reuses": run.numeric.counts.get("reuse", 0),
        "reference": reference.to_json(),
        "minimum_total_stage_executions": reference.minimum_executions + 1,
        "excess_stage_executions": execution_count - reference.minimum_executions - 1,
        "interpretation_ns": run.interpretation_ns,
        "numeric_policy_wall_ns": run.numeric.finished_ns - run.numeric.started_ns,
        "composition_ns": run.composition_ns,
        "runtime_wall_ns": run.wall_ns,
        "numeric_operation_counts": dict(run.numeric.counts),
        "nested_operation_duration_ns": dict(run.numeric.durations),
        "b2_recomputed_role_checks": run.numeric.counts.get("contract_checks", 0),
        "evaluation_and_reference_ns": perf_counter_ns() - started,
        "transformations": 1,
        "fallback_executions": 0,
        "human_questions_during_replay": 0,
        "source_experiment_reruns": 0,
        "evaluated_model_calls": 0,
        "evaluated_model_tokens": 0,
        "external_model_api_cost_usd": 0,
        "local_resource_cost_usd": None,
        "report_path": str(run.document),
        "output_sha256": digest(final),
    }
