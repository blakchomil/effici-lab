"""Typed parsers for the deliberately narrow development data contract."""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass
from datetime import date
from typing import Final

from .model import Context, InputError, Json, Requirements, decode_json

SCHEMA: Final = ("date", "category", "amount_cents")


def iso_date(value: str) -> str:
    """Parse ISO dates and return their canonical spelling."""
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise InputError("date", f"unsupported date {value!r}") from exc


@dataclass(frozen=True, slots=True)
class Record:
    """One source record with the original CSV strings retained."""

    day: str
    category: str
    amount: str

    def normalized(self) -> Json:
        return {
            "date": iso_date(self.day),
            "category": self.category,
            "amount_cents": int(self.amount),
        }

    def raw(self) -> Json:
        return {"date": self.day, "category": self.category, "amount_cents": self.amount}


def source_records(source: bytes) -> tuple[Record, ...]:
    """Read all CSV rows, rejecting unsupported schemas and scalar values."""
    try:
        rows = list(csv.reader(io.StringIO(source.decode("utf-8")), strict=True))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise InputError("source", str(exc)) from exc
    if not rows or tuple(rows[0]) != SCHEMA:
        raise InputError("schema", "expected date,category,amount_cents")
    result: list[Record] = []
    for row in rows[1:]:
        if len(row) != len(SCHEMA):
            raise InputError("row", "expected exactly three columns")
        day, category, amount = row
        _ = iso_date(day)
        if not category or "\n" in category or "\r" in category:
            raise InputError("category", "expected nonempty single-line category")
        if re.fullmatch(r"[+-]?[0-9]+", amount) is None:
            raise InputError("amount_cents", "expected integer cents")
        result.append(Record(day, category, amount))
    return tuple(result)


def snapshot(context: Context, records: list[Json]) -> Json:
    return {
        "dataset_id": context.dataset_id,
        "source_sha256": context.source_sha256,
        "schema": list(SCHEMA),
        "rows": records,
    }


def json_content(content: bytes) -> Json:
    """Decode a UTF-8 JSON artifact at its trust boundary."""
    try:
        return decode_json(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError("artifact", "malformed UTF-8 JSON") from exc


def records_content(content: bytes, *, normalized: bool) -> tuple[Record, ...]:
    """Parse supported snapshot rows without silently coercing malformed types."""
    value = json_content(content)
    if not isinstance(value, dict) or value.get("schema") != list(SCHEMA):
        raise InputError("schema", "unsupported snapshot schema")
    rows = value.get("rows")
    if not isinstance(rows, list):
        raise InputError("rows", "expected row array")
    records: list[Record] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(SCHEMA):
            raise InputError("row", "unsupported row schema")
        day, category, amount = row["date"], row["category"], row["amount_cents"]
        if not isinstance(day, str) or not isinstance(category, str):
            raise InputError("row", "date and category must be strings")
        if normalized:
            if type(amount) is not int:
                raise InputError("amount_cents", "normalized cents must be integers")
        elif not isinstance(amount, str) or re.fullmatch(r"[+-]?[0-9]+", amount) is None:
            raise InputError("amount_cents", "raw cents must be integer strings")
        _ = iso_date(day)
        records.append(Record(day, category, str(amount)))
    return tuple(records)


@dataclass(frozen=True, slots=True)
class Aggregate:
    """Typed aggregate with its semantic context."""

    dataset_id: str
    source_sha256: str
    start: str
    end: str
    totals: tuple[tuple[str, int], ...]

    def to_json(self) -> Json:
        totals: dict[str, Json] = dict(self.totals)
        return {
            "dataset_id": self.dataset_id,
            "source_sha256": self.source_sha256,
            "period": {"start_inclusive": self.start, "end_exclusive": self.end},
            "group_by": ["category"],
            "metric": {"operation": "sum", "field": "amount_cents", "unit": "cents"},
            "totals_cents": totals,
        }

    def labels(self, language: str) -> tuple[tuple[str, str], ...]:
        return (
            ("Language", language),
            ("Dataset", self.dataset_id),
            ("Source SHA256", self.source_sha256),
            ("Period", f"[{self.start}, {self.end})"),
            ("Group by", "category"),
            ("Metric", "sum(amount_cents)"),
            ("Unit", "cents"),
        )


def aggregate_content(content: bytes) -> Aggregate:
    """Parse the aggregate schema, including its grouping and metric semantics."""
    value = json_content(content)
    if not isinstance(value, dict):
        raise InputError("aggregate", "expected object")
    dataset, source = value.get("dataset_id"), value.get("source_sha256")
    period, totals = value.get("period"), value.get("totals_cents")
    if not isinstance(dataset, str) or not isinstance(source, str):
        raise InputError("aggregate", "missing dataset provenance")
    if not isinstance(period, dict) or not isinstance(totals, dict):
        raise InputError("aggregate", "missing period or totals")
    start, end = period.get("start_inclusive"), period.get("end_exclusive")
    if not isinstance(start, str) or not isinstance(end, str):
        raise InputError("period", "expected date strings")
    pairs: list[tuple[str, int]] = []
    for key, amount in sorted(totals.items()):
        if type(amount) is not int:
            raise InputError("totals_cents", "expected integer values")
        pairs.append((key, amount))
    aggregate = Aggregate(dataset, source, iso_date(start), iso_date(end), tuple(pairs))
    if value != aggregate.to_json():
        raise InputError("aggregate", "unsupported aggregation semantics")
    return aggregate


def sum_records(records: tuple[Record, ...], target: Requirements) -> tuple[tuple[str, int], ...]:
    start, end = iso_date(target.start), iso_date(target.end)
    if start >= end:
        raise InputError("period", "start must precede end")
    totals: dict[str, int] = {}
    for row in records:
        if start <= iso_date(row.day) < end:
            totals[row.category] = totals.get(row.category, 0) + int(row.amount)
    return tuple(sorted(totals.items()))
