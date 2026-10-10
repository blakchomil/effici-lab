"""Typed frozen facts and interpretations shared by composition and audit."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from src.intent_revalidation.model import Json

FACT_KEYS: Final = (
    "license",
    "ci",
    "release",
    "external_reproduction",
    "ai_advantage",
)


@dataclass(frozen=True, slots=True)
class Fact:
    """One visible fact with the exact supporting evidence reference."""

    key: str
    value: str
    evidence: str

    def to_json(self) -> Json:
        return {"key": self.key, "value": self.value, "evidence": self.evidence}


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Frozen observed repository facts, distinct from historical case inputs."""

    captured_at: str
    repository_revision: str
    facts: tuple[Fact, ...]
    content: bytes
    sha256: str


class Control(StrEnum):
    """Equal-information interpretation strategies for the recorded response."""

    RULE = "rule"
    CLARIFICATION = "clarification"


class Meaning(StrEnum):
    """The two disclosed clarification choices, with unresolved as a real outcome."""

    READINESS = "readiness"
    PERFORMANCE = "performance"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class Choice:
    """A labelled meaning and the option text actually shown to the human."""

    meaning: Meaning
    text: str


@dataclass(frozen=True, slots=True)
class Clarification:
    """An observed question/response, without a researcher-imputed answer."""

    question: str
    choices: tuple[Choice, ...]
    answer: str | None
    human_confirmed: bool
    content: bytes
    sha256: str


@dataclass(frozen=True, slots=True)
class Interpretation:
    """A control's result; recorded answer use is not a new human interaction."""

    meaning: Meaning
    answer_records_used: int
    unresolved_fields: tuple[str, ...]

    def to_json(self) -> Json:
        return {
            "meaning": self.meaning.value,
            "answer_records_used": self.answer_records_used,
            "unresolved_fields": list(self.unresolved_fields),
        }
