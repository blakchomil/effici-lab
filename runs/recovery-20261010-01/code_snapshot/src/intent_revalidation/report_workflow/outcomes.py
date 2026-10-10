"""Record policy costs separately from post-execution evaluation overhead."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.intent_revalidation.model import Json
    from src.intent_revalidation.policies import Policy

    from .audit import Audit
    from .cache import Result
    from .model import Revision
    from .reference import ReferenceResult


@dataclass(frozen=True, slots=True)
class Outcome:
    """Policy work and evaluator overhead remain separately measured."""

    revision: Revision
    policy: Policy
    result: Result
    audit: Audit
    reference: ReferenceResult
    evaluation_ns: int

    def to_json(self) -> Json:
        return {
            "revision": self.revision.revision_id,
            "requirements": self.revision.requirements.to_json(),
            "policy": self.policy.value,
            "operation_counts": dict(self.result.counts),
            "operation_duration_ns": dict(self.result.durations),
            "policy_wall_ns": self.result.finished_ns - self.result.started_ns,
            "evaluation_and_reference_ns": self.evaluation_ns,
            "audit": self.audit.to_json(),
            "reference": self.reference.to_json(),
            "excess_executions_over_reference": self.result.counts.get("executions", 0)
            - self.reference.minimum_executions,
            "artifact_ids": [item.artifact_id for item in self.result.artifacts],
            "report_path": str(self.result.artifacts[-1].path),
            "source_experiment_reruns": 0,
            "inference_calls": 0,
            "tokens": 0,
            "external_api_cost_usd": 0,
            "local_resource_dollar_cost": None,
        }
