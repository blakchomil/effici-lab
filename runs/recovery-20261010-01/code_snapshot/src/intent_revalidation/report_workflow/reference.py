"""Evaluator-only exhaustive execution-count bound for the three report operations."""

from dataclasses import dataclass
from itertools import product

from src.intent_revalidation.model import Json, Validity, digest

from .evaluation import evaluate, source_oracle
from .model import Artifact, Context, ReportRequirements, Step


@dataclass(frozen=True, slots=True)
class ReferenceResult:
    """Finite execution-count result unavailable to the selection policies."""

    minimum_executions: int
    valid_plans: int
    enumerated_plans: int
    minimum_actions: tuple[str, ...]

    def to_json(self) -> Json:
        return {
            "minimum_executions": self.minimum_executions,
            "valid_plans": self.valid_plans,
            "enumerated_plans": self.enumerated_plans,
            "minimum_actions": list(self.minimum_actions),
            "execution_cost_per_stage": 1,
            "scope": "current-cache three-stage execution-count lower bound; evaluator-only",
        }


def enumerate_plans(
    cache: tuple[Artifact, ...], target: ReportRequirements, context: Context
) -> ReferenceResult:
    """Enumerate current cache candidates and one fresh execution per operation."""
    oracle = source_oracle(target, context)
    fresh = {Step.SELECT: digest(oracle.selected), Step.SUMMARY: digest(oracle.summary)}
    valid = {item: evaluate(item, target, context).validity for item in cache}
    choices: tuple[tuple[Artifact | None, ...], ...] = tuple(
        (*tuple(item for item in cache if item.step == step), None) for step in Step
    )
    minimum = len(Step)
    actions = tuple(f"execute:{step.value}" for step in Step)
    feasible_count = enumerated = 0
    for plan in product(*choices):
        enumerated += 1
        previous = context.source.sha256
        executions = 0
        candidate_actions: list[str] = []
        feasible = True
        for step, cached in zip(Step, plan, strict=True):
            if cached is None:
                executions += 1
                previous = fresh.get(step, "terminal")
                candidate_actions.append(f"execute:{step.value}")
            else:
                if valid[cached] != Validity.VALID or cached.input_hash != previous:
                    feasible = False
                    break
                previous = cached.sha256
                candidate_actions.append(f"reuse:{step.value}:{cached.artifact_id}")
        if feasible:
            feasible_count += 1
            if executions < minimum:
                minimum, actions = executions, tuple(candidate_actions)
    return ReferenceResult(minimum, feasible_count, enumerated, actions)
