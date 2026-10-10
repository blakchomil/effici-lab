"""Parse only structured policy inputs; development expectations stay outside policy state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import TYPE_CHECKING, assert_never

from .model import (
    InputError,
    Json,
    JsonObject,
    Requirements,
    Revision,
    RevisionId,
    Task,
    decode_json,
)

if TYPE_CHECKING:
    from pathlib import Path


def mapping(value: Json) -> JsonObject:
    """Parse a JSON object at the boundary."""
    match value:
        case dict() as result:
            return result
        case None | bool() | int() | float() | str() | list():
            raise InputError("JSON", "expected object")
        case unreachable:
            assert_never(unreachable)


def sequence(value: Json) -> list[Json]:
    """Parse a JSON array at the boundary."""
    match value:
        case list() as result:
            return result
        case None | bool() | int() | float() | str() | dict():
            raise InputError("JSON", "expected array")
        case unreachable:
            assert_never(unreachable)


def string(value: Json) -> str:
    """Parse a JSON string at the boundary."""
    match value:
        case str() as result:
            return result
        case None | bool() | int() | float() | list() | dict():
            raise InputError("JSON", "expected string")
        case unreachable:
            assert_never(unreachable)


def field(record: JsonObject, key: str) -> Json:
    """Reject a missing structured requirement field."""
    if key not in record:
        raise InputError(key, "missing field")
    return record[key]


def parse_requirements(value: Json) -> Requirements:
    """Reject unsupported semantics instead of silently projecting them away."""
    record = mapping(value)
    period = mapping(field(record, "period"))
    output = mapping(field(record, "output"))
    start = string(field(period, "start_inclusive"))
    end = string(field(period, "end_exclusive"))
    try:
        start_date, end_date = date.fromisoformat(start), date.fromisoformat(end)
    except ValueError as error:
        raise InputError("period", "expected ISO dates") from error
    if start_date.isoformat() != start or end_date.isoformat() != end or start_date >= end_date:
        raise InputError("period", "expected canonical dates and nonempty half-open interval")
    if field(record, "group_by") != ["category"]:
        raise InputError("group_by", "Phase 1 supports only category")
    if field(record, "metric") != {"operation": "sum", "field": "amount_cents", "unit": "cents"}:
        raise InputError("metric", "Phase 1 supports only sum(amount_cents) in cents")
    output_format = string(field(output, "format"))
    if output_format not in {"markdown", "html"}:
        raise InputError("output.format", "supported values: markdown, html")
    language = string(field(output, "language"))
    if language != "en":
        raise InputError("output.language", "Phase 1 supports only en")
    title = string(field(output, "title"))
    dataset_id = string(field(record, "dataset_id"))
    if not title or any(char in title for char in "\r\n|"):
        raise InputError(
            "output.title", "expected nonempty single-line title without table delimiter"
        )
    if not dataset_id or any(char in dataset_id for char in "\r\n|"):
        raise InputError("dataset_id", "expected nonempty single-line identifier")
    return Requirements(dataset_id, start, end, output_format, language, title)


def parse_revision(value: Json, change: str) -> Revision:
    record = mapping(value)
    parent = field(record, "parent_id")
    return Revision(
        RevisionId(string(field(record, "id"))),
        None if parent is None else RevisionId(string(parent)),
        parse_requirements(field(record, "requirements")),
        change,
    )


@dataclass(frozen=True, slots=True)
class ReplayEvent:
    """A replay event declares order, never fabricated wall-clock duration."""

    sequence: int
    kind: ReplayKind
    task: Task | None
    attempt_id: str | None


class ReplayKind(StrEnum):
    """The three supported events in an ordered development replay."""

    START = "run_started"
    CHANGE = "requirements_changed"
    COMPLETE = "run_completed"


@dataclass(frozen=True, slots=True)
class Case:
    """Only policy-visible structured inputs, without expected labels or totals."""

    id: str
    description: str
    completed_tasks: tuple[Task, ...]
    target: Revision
    events: tuple[ReplayEvent, ...]


@dataclass(frozen=True, slots=True)
class Suite:
    """The public development experiment inputs."""

    dataset_id: str
    source_path: Path
    initial: Revision
    cases: tuple[Case, ...]


def _parse_events(
    record: JsonObject, tasks: tuple[Task, ...], initial: Revision, target: Revision
) -> tuple[ReplayEvent, ...]:
    values = [mapping(entry) for entry in sequence(record.get("event_sequence", []))]
    events: list[ReplayEvent] = []
    for index, event in enumerate(values, 1):
        if field(event, "sequence") != index:
            raise InputError("event_sequence", "expected contiguous order")
        kind = ReplayKind(string(field(event, "type")))
        task = Task(string(field(event, "task_id"))) if "task_id" in event else None
        attempt_id = string(field(event, "attempt_id")) if "attempt_id" in event else None
        events.append(ReplayEvent(index, kind, task, attempt_id))
    if events:
        if [event.kind for event in events] != list(ReplayKind):
            raise InputError("event_sequence", "only start/change/complete replay is supported")
        if (
            events[0].task != events[2].task
            or events[0].attempt_id != events[2].attempt_id
            or events[0].task is None
            or events[0].attempt_id is None
            or events[0].task in tasks
        ):
            raise InputError("event_sequence", "invalid late attempt identity")
        if (
            values[0].get("revision_id") != initial.id
            or values[1].get("target_revision_id") != target.id
            or values[2].get("started_revision_id") != initial.id
        ):
            raise InputError("event_sequence", "revision identity mismatch")
        if record.get("policy_activation") != "after_all_events_in_event_sequence_complete":
            raise InputError("policy_activation", "policy must start after the complete replay")
    return tuple(events)


def _parse_case(value: Json, initial: Revision) -> Case:
    record = mapping(value)
    state = mapping(field(record, "initial_state"))
    tasks = tuple(Task(string(task)) for task in sequence(field(state, "completed_tasks")))
    if tasks != tuple(Task)[: len(tasks)] or field(state, "in_flight_attempt") is not None:
        raise InputError("initial_state", "expected completed prefix and no in-flight attempt")
    target = parse_revision(field(record, "target_revision"), string(field(record, "user_change")))
    if target.parent_id != initial.id or target.id == initial.id:
        raise InputError("target_revision", "expected new child of initial revision")
    identifier = string(field(record, "id"))
    if not identifier or any(
        char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        for char in identifier
    ):
        raise InputError("case.id", "expected safe folder name")
    return Case(
        identifier,
        string(field(record, "description")),
        tasks,
        target,
        _parse_events(record, tasks, initial, target),
    )


def load_suite(path: Path) -> Suite:
    """Validate the supported linear replay scenario before any policy runs."""
    root = mapping(decode_json(path.read_text(encoding="utf-8")))
    if field(root, "format_version") != 1:
        raise InputError("format_version", "expected 1")
    dataset = mapping(field(root, "dataset"))
    initial = parse_revision(field(root, "initial_revision"), "initial requirements")
    cases = [_parse_case(value, initial) for value in sequence(field(root, "cases"))]
    ids = [case.id for case in cases]
    if len(ids) != len(set(ids)) or not cases:
        raise InputError("cases", "expected nonempty unique case IDs")
    dataset_id = string(field(dataset, "id"))
    if any(
        revision.requirements.dataset_id != dataset_id
        for revision in (initial, *(case.target for case in cases))
    ):
        raise InputError("dataset_id", "only the fixed suite source is supported")
    return Suite(dataset_id, path.parent / string(field(dataset, "path")), initial, tuple(cases))
