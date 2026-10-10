from dataclasses import replace
from typing import Final

import pytest

from src.intent_revalidation.model import InputError
from src.intent_revalidation.readiness_workflow.composition import compose
from src.intent_revalidation.readiness_workflow.interpretation import interpret
from src.intent_revalidation.readiness_workflow.model import (
    Choice,
    Clarification,
    Control,
    Fact,
    Interpretation,
    Meaning,
    Snapshot,
)

RECORD: Final = Clarification(
    "Choose the report target",
    (Choice(Meaning.READINESS, "준비 현황"), Choice(Meaning.PERFORMANCE, "Measured results")),
    "준비 현황",
    human_confirmed=True,
    content=b"recorded transcript",
    sha256="record-hash",
)
SNAPSHOT: Final = Snapshot(
    "2026-10-10T00:00:00Z",
    "repository-revision",
    (Fact("license", "MIT", "LICENSE"), Fact("ci", "passed", "ci-evidence.json")),
    b"frozen facts",
    "facts-hash",
)


@pytest.mark.parametrize("choice", RECORD.choices)
def test_controls_agree_when_confirmed_answer_is_exact_disclosed_text(choice: Choice) -> None:
    # Given: labels differ from the actual recorded answer texts.
    record = replace(RECORD, answer=choice.text)
    # When: both controls receive the identical complete record.
    results = tuple(interpret(record, control) for control in Control)
    # Then: each uses one actual answer and resolves its disclosed meaning.
    assert results == (Interpretation(choice.meaning, 1, ()),) * len(Control)


@pytest.mark.parametrize(
    ("record", "unresolved_field"),
    [
        (replace(RECORD, answer=None), "answer"),
        (replace(RECORD, answer=""), "answer"),
        (replace(RECORD, human_confirmed=False), "human_confirmed"),
        (replace(RECORD, answer="readiness"), "answer"),
        (replace(RECORD, answer="준비 현황 "), "answer"),
        (replace(RECORD, answer="준비 현황; Measured results"), "answer"),
        (replace(RECORD, question=""), "question"),
        (replace(RECORD, choices=()), "choices"),
        (replace(RECORD, choices=(RECORD.choices[0],) * 2), "choices"),
        (
            replace(RECORD, choices=(RECORD.choices[0], Choice(Meaning.PERFORMANCE, "준비 현황"))),
            "choices",
        ),
        (
            replace(RECORD, choices=(RECORD.choices[0], Choice(Meaning.READINESS, "Other"))),
            "choices",
        ),
        (
            replace(RECORD, choices=(RECORD.choices[0], Choice(Meaning.UNRESOLVED, "Other"))),
            "choices",
        ),
    ],
)
def test_controls_remain_unresolved_when_record_is_incomplete_or_conflicting(
    record: Clarification, unresolved_field: str
) -> None:
    # Given: an absent, unconfirmed, unsupported or conflicting response.
    expected = Interpretation(Meaning.UNRESOLVED, 0, (unresolved_field,))
    # When: both controls process the same record.
    results = tuple(interpret(record, control) for control in Control)
    # Then: neither guesses a target or counts a question as an answer.
    assert all(result.meaning == expected.meaning for result in results)
    assert all(result.answer_records_used == 0 for result in results)
    assert all(unresolved_field in result.unresolved_fields for result in results)
    assert len(set(results)) == 1


def test_composition_preserves_numeric_bytes_and_frozen_facts() -> None:
    # Given: a report containing non-ASCII bytes, CRLF and significant whitespace.
    numeric = "# 수치\r\n| B1 | 0.125 |\n  preserved  \n".encode()
    # When: readiness facts are composed around the report.
    result = compose(numeric, SNAPSHOT, "source-hash")
    # Then: the exact byte framing and provenance contract remains parseable.
    prefix, remainder = result.split(b"<!-- numeric:start -->\n", maxsplit=1)
    preserved, suffix = remainder.rsplit(b"<!-- numeric:end -->\n", maxsplit=1)
    assert preserved == numeric
    assert suffix == b""
    lines = prefix.decode().splitlines()
    assert lines[2:6] == [
        f"Snapshot UTC: {SNAPSHOT.captured_at}",
        f"Repository revision: {SNAPSHOT.repository_revision}",
        "Source SHA256: source-hash",
        f"Facts SHA256: {SNAPSHOT.sha256}",
    ]
    assert lines[9:11] == ["| license | MIT | LICENSE |", "| ci | passed | ci-evidence.json |"]


@pytest.mark.parametrize("numeric", [b"", b"unterminated", b"report\r"])
def test_composition_rejects_report_without_trailing_newline(numeric: bytes) -> None:
    # Given: bytes cannot be framed without changing the report or delimiter.
    # When: composing an unterminated report.
    with pytest.raises(InputError) as caught:
        _ = compose(numeric, SNAPSHOT, "source-hash")
    # Then: the caller gets the structured input failure.
    assert caught.value.field == "numeric_report"
