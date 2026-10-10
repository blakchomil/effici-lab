from dataclasses import dataclass
from pathlib import Path
from typing import Final

from src.intent_revalidation.fixtures import mapping, sequence
from src.intent_revalidation.model import JsonObject, decode_json
from src.intent_revalidation.recovery_workflow.model import Outcome
from src.intent_revalidation.recovery_workflow.study import run_study

SOURCE: Final = Path(__file__).parents[1] / "runs/phase1-20261010-01/metrics.json"


@dataclass(frozen=True, slots=True)
class Trace:
    root: Path
    outcomes: tuple[Outcome, ...]
    source: bytes

    def arm(self, outcome: Outcome) -> Path:
        return self.root / f"repeat-{outcome.repeat}" / outcome.policy.value

    def event(self, outcome: Outcome) -> Path:
        return self.arm(outcome) / "events" / outcome.event.event_id


def run_trace(destination: Path) -> Trace:
    source = SOURCE.read_bytes()
    outcomes = run_study(SOURCE, destination, "pytest recovery integration")
    assert SOURCE.read_bytes() == source
    return Trace(destination, outcomes, source)


def records(path: Path) -> tuple[JsonObject, ...]:
    return tuple(mapping(decode_json(line)) for line in path.read_text().splitlines())


def array_records(path: Path) -> tuple[JsonObject, ...]:
    return tuple(mapping(item) for item in sequence(decode_json(path.read_text())))
