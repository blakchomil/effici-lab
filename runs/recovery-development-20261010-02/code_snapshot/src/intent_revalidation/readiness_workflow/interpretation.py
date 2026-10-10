"""Resolve disclosed choices without guessing a natural-language report target."""

from __future__ import annotations

from typing import TYPE_CHECKING, assert_never

from .model import Control, Interpretation, Meaning

if TYPE_CHECKING:
    from .model import Clarification


def interpret(record: Clarification, control: Control) -> Interpretation:
    """Both controls consume the same exact confirmed choice text, without inference.

    These deterministic controls share validation and resolution deliberately: a
    recorded answer is one consumed record, never a newly asked question.
    """
    match control:
        case Control.RULE | Control.CLARIFICATION:
            unresolved: list[str] = []
            if not record.question.strip():
                unresolved.append("question")
            texts = {choice.text for choice in record.choices}
            meanings = {choice.meaning for choice in record.choices}
            supported = {Meaning.READINESS, Meaning.PERFORMANCE}
            if (
                len(record.choices) != len(supported)
                or len(texts) != len(supported)
                or meanings != supported
                or any(not text.strip() for text in texts)
            ):
                unresolved.append("choices")
            if not record.human_confirmed:
                unresolved.append("human_confirmed")
            if record.answer is None or record.answer not in texts:
                unresolved.append("answer")
            if unresolved:
                return Interpretation(Meaning.UNRESOLVED, 0, tuple(unresolved))
            selected = next(choice for choice in record.choices if choice.text == record.answer)
            return Interpretation(selected.meaning, 1, ())
        case unreachable:
            assert_never(unreachable)
