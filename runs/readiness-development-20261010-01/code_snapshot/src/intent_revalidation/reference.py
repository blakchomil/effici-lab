"""Exhaustive evaluator-only execution-count lower bound for the four-stage DAG."""

from dataclasses import dataclass
from itertools import product
from typing import Final

from .evaluation import evaluate, source_oracle
from .model import TASKS, Artifact, Context, Json, Requirements, Validity, digest

EXECUTION_COST: Final = 1


@dataclass(frozen=True, slots=True)
class ReferenceResult:
    """Finite-model lower bound, not a hardware-time optimum or policy input."""

    minimum_executions: int
    valid_plans: int
    enumerated_plans: int
    minimum_actions: tuple[str, ...]

    def to_json(self) -> Json:
        """Expose the counting assumptions with the exhaustive result."""
        return {
            "minimum_executions": self.minimum_executions,
            "valid_plans": self.valid_plans,
            "enumerated_plans": self.enumerated_plans,
            "minimum_actions": list(self.minimum_actions),
            "execution_cost_per_stage": EXECUTION_COST,
            "scope": "current-cache four-stage execution-count lower bound; evaluator-only",
        }


def enumerate_plans(
    cache: tuple[Artifact, ...],
    target: Requirements,
    context: Context,
) -> ReferenceResult:
    """Enumerate each existing artifact or one fresh execution per logical stage."""
    oracle = source_oracle(target, context)
    fresh_hashes = {task: digest(oracle.content(task)) for task in TASKS[:-1]}
    validity = {item: evaluate(item, target, context).validity for item in cache}
    choices: tuple[tuple[Artifact | None, ...], ...] = tuple(
        (*tuple(item for item in cache if item.task == task), None) for task in TASKS
    )
    minimum = len(TASKS) * EXECUTION_COST
    minimum_actions = tuple(f"execute:{task.value}" for task in TASKS)
    valid_plans = enumerated = 0
    for plan in product(*choices):
        enumerated += 1
        previous: tuple[str, ...] = ()
        actions: list[str] = []
        executions = 0
        feasible = True
        for task, cached in zip(TASKS, plan, strict=True):
            if cached is None:
                executions += EXECUTION_COST
                actions.append(f"execute:{task.value}")
                previous = (fresh_hashes.get(task, "terminal"),)
            else:
                if validity[cached] != Validity.VALID or cached.input_hashes != previous:
                    feasible = False
                    break
                actions.append(f"reuse:{task.value}:{cached.id}")
                previous = (cached.sha256,)
        if feasible:
            valid_plans += 1
            if executions < minimum:
                minimum, minimum_actions = executions, tuple(actions)
    return ReferenceResult(minimum, valid_plans, enumerated, minimum_actions)
