"""Parse the observed metrics before any output directory is created."""

from __future__ import annotations

from typing import TYPE_CHECKING, assert_never

from src.intent_revalidation.fixtures import field, mapping, sequence, string
from src.intent_revalidation.model import InputError, Json, decode_json, digest
from src.intent_revalidation.policies import Policy

from .model import MetricRow, Source

if TYPE_CHECKING:
    from pathlib import Path


def count(value: Json) -> int:
    match value:
        case bool():
            raise InputError("count", "boolean is not an integer count")
        case int() as result:
            if result < 0:
                raise InputError("count", "expected nonnegative integer")
            return result
        case None | float() | str() | list() | dict():
            raise InputError("count", "expected integer")
        case unreachable:
            assert_never(unreachable)


def boolean(value: Json) -> bool:
    match value:
        case bool() as result:
            return result
        case None | int() | float() | str() | list() | dict():
            raise InputError("validity", "expected boolean")
        case unreachable:
            assert_never(unreachable)


def parse_row(value: Json) -> MetricRow:
    row = mapping(value)
    audit = mapping(field(row, "audit"))
    counts = mapping(field(row, "operation_counts"))
    case_id = string(field(row, "case_id"))
    if not case_id or not case_id.isalnum():
        raise InputError("case_id", "expected nonempty alphanumeric ID")
    try:
        policy = Policy(string(field(row, "policy")))
    except ValueError as error:
        raise InputError("policy", "expected B0, B1 or B2") from error
    return MetricRow(
        case_id,
        policy,
        boolean(field(audit, "final_satisfied")),
        count(counts.get("policy_executions", 0)),
        count(field(audit, "invalid_reuse_events")),
    )


def parse_source(content: bytes) -> Source:
    rows = tuple(parse_row(value) for value in sequence(decode_json(content.decode())))
    identities = {(row.case_id, row.policy) for row in rows}
    cases = {row.case_id for row in rows}
    if not rows or len(identities) != len(rows):
        raise InputError("metrics", "empty or duplicate case-policy rows")
    if identities != {(case_id, policy) for case_id in cases for policy in Policy}:
        raise InputError("metrics", "every case requires exactly B0, B1 and B2")
    return Source(
        content, digest(content), tuple(sorted(rows, key=lambda row: (row.case_id, row.policy)))
    )


def load_source(path: Path) -> Source:
    return parse_source(path.read_bytes())
