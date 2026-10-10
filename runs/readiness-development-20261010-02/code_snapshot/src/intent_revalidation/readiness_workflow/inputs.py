"""Parse frozen facts and actual human clarification at the input boundary."""

from __future__ import annotations

from typing import assert_never

from src.intent_revalidation.fixtures import field, mapping, sequence, string
from src.intent_revalidation.model import InputError, Json, decode_json, digest
from src.intent_revalidation.report_workflow.inputs import boolean

from .model import FACT_KEYS, Choice, Clarification, Fact, Meaning, Snapshot


def plain(value: Json) -> str:
    """Accept one literal Markdown cell, without active markup or delimiters."""
    text = string(value)
    if not text.strip() or any(char in text for char in "\n\r|<>`*_[]\\"):
        raise InputError("facts", "expected plain nonempty single-line cell")
    return text


def parse_snapshot(content: bytes) -> Snapshot:
    """Bind typed facts to their exact original bytes before policy execution."""
    record = mapping(decode_json(content.decode("utf-8")))
    facts: list[Fact] = []
    for value in sequence(field(record, "facts")):
        row = mapping(value)
        facts.append(
            Fact(
                string(field(row, "key")), plain(field(row, "value")), plain(field(row, "evidence"))
            )
        )
    keys = [fact.key for fact in facts]
    if len(keys) != len(FACT_KEYS) or set(keys) != set(FACT_KEYS):
        raise InputError("facts", "expected all five unique evidence fields")
    return Snapshot(
        plain(field(record, "captured_at")),
        plain(field(record, "repository_revision")),
        tuple(facts),
        content,
        digest(content),
    )


def parse_clarification(content: bytes) -> Clarification:
    """Preserve an absent response; never convert unanswered options into consent."""
    record = mapping(decode_json(content.decode("utf-8")))
    choices: list[Choice] = []
    for value in sequence(field(record, "choices")):
        row = mapping(value)
        try:
            meaning = Meaning(string(field(row, "meaning")))
        except ValueError as error:
            raise InputError("meaning", "unsupported clarification option") from error
        choices.append(Choice(meaning, string(field(row, "text"))))
    answer = field(record, "answer")
    match answer:
        case None:
            text = None
        case str() as response:
            text = response
        case bool() | int() | float() | list() | dict():
            raise InputError("answer", "expected a response string or null")
        case unreachable:
            assert_never(unreachable)
    return Clarification(
        string(field(record, "question")),
        tuple(choices),
        text,
        boolean(field(record, "human_confirmed")),
        content,
        digest(content),
    )
