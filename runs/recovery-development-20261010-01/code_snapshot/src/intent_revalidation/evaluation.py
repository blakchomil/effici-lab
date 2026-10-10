"""Independent source arithmetic and visible-content oracle, unavailable to policies."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date
from html import escape
from html.parser import HTMLParser
from typing import Final, assert_never, override

from .model import (
    Artifact,
    Check,
    Context,
    InputError,
    Json,
    Requirements,
    Task,
    Validity,
    canonical,
    decode_json,
    digest,
)

_MARKDOWN_CONTEXT_LINES: Final = 10
_MARKDOWN_CELL_COUNT: Final = 4


@dataclass(frozen=True, slots=True)
class Oracle:
    """Complete snapshots computed directly from the source CSV."""

    raw: Json
    normalized: Json
    aggregate: Json
    totals: tuple[tuple[str, int], ...]

    def content(self, task: Task) -> bytes:
        """Predict fresh intermediate bytes without calling production stages."""
        match task:
            case Task.LOAD:
                return canonical(self.raw)
            case Task.NORMALIZE:
                return canonical(self.normalized)
            case Task.AGGREGATE:
                return canonical(self.aggregate)
            case Task.RENDER:
                message = "terminal report hash is not needed for planning"
                msg = "oracle"
                raise InputError(msg, message)
            case unreachable:
                assert_never(unreachable)


def source_oracle(target: Requirements, context: Context) -> Oracle:
    """Read the fixed source snapshot independently and preserve every record."""
    source_hash = digest(context.source)
    if source_hash != context.source_sha256 or target.dataset_id != context.dataset_id:
        message = "snapshot fingerprint or dataset mismatch"
        msg = "source"
        raise InputError(msg, message)
    raw_rows: list[Json] = []
    normalized_rows: list[Json] = []
    totals: dict[str, int] = {}
    reader = csv.reader(io.StringIO(context.source.decode("utf-8")))
    schema = ["date", "category", "amount_cents"]
    if next(reader, None) != schema:
        message = "unexpected columns"
        msg = "CSV"
        raise InputError(msg, message)
    start, end = date.fromisoformat(target.start), date.fromisoformat(target.end)
    for row in reader:
        if len(row) != len(schema):
            message = "unexpected row width"
            msg = "CSV"
            raise InputError(msg, message)
        day, category, amount = row
        parsed_day, cents = date.fromisoformat(day), int(amount)
        raw_rows.append({"date": day, "category": category, "amount_cents": amount})
        normalized_rows.append(
            {
                "date": parsed_day.isoformat(),
                "category": category,
                "amount_cents": cents,
            }
        )
        if start <= parsed_day < end:
            totals[category] = totals.get(category, 0) + cents
    base: dict[str, Json] = {"dataset_id": target.dataset_id, "source_sha256": source_hash}
    raw: Json = {**base, "schema": list(schema), "rows": raw_rows}
    normalized: Json = {**base, "schema": list(schema), "rows": normalized_rows}
    aggregate: Json = {
        **base,
        "period": {"start_inclusive": target.start, "end_exclusive": target.end},
        "group_by": ["category"],
        "metric": {"operation": "sum", "field": "amount_cents", "unit": "cents"},
        "totals_cents": dict(sorted(totals.items())),
    }
    return Oracle(raw, normalized, aggregate, tuple(sorted(totals.items())))


class _HtmlTokens(HTMLParser):
    """Parse markup structure, attributes and visible text rather than metadata."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tokens: list[tuple[str, ...]] = []

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tokens.append(("start", tag, *(f"{key}={value}" for key, value in sorted(attrs))))

    @override
    def handle_endtag(self, tag: str) -> None:
        self.tokens.append(("end", tag))

    @override
    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag != "meta":
            self.handle_endtag(tag)

    @override
    def handle_data(self, data: str) -> None:
        if data.strip():
            self.tokens.append(("text", data.strip()))


def _metadata(target: Requirements, context: Context) -> tuple[tuple[str, str], ...]:
    return (
        ("Language", target.language),
        ("Dataset", target.dataset_id),
        ("Source SHA256", context.source_sha256),
        ("Period", f"[{target.start}, {target.end})"),
        ("Group by", "category"),
        ("Metric", "sum(amount_cents)"),
        ("Unit", "cents"),
    )


def _html_expected(target: Requirements, context: Context, oracle: Oracle) -> str:
    metadata = "".join(
        f"<dt>{escape(label)}</dt><dd>{escape(value)}</dd>"
        for label, value in _metadata(target, context)
    )
    rows = "".join(
        f"<tr><td>{escape(category)}</td><td>{amount}</td></tr>"
        for category, amount in oracle.totals
    )
    title = escape(target.title)
    return (
        f'<html lang="{escape(target.language)}"><head><meta charset="utf-8">'
        f"<title>{title}</title></head><body><h1>{title}</h1><dl>{metadata}</dl>"
        "<table><thead><tr><th>category</th><th>amount_cents</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></body></html>"
    )


def _markdown_fields(text: str) -> tuple[tuple[str, ...], tuple[tuple[str, int], ...]]:
    """Parse the supported heading, context lines and integer table grammar."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < _MARKDOWN_CONTEXT_LINES or not lines[0].startswith("# "):
        message = "missing heading or context"
        msg = "Markdown"
        raise InputError(msg, message)
    if lines[8:10] != ["| category | amount_cents |", "| --- | ---: |"]:
        message = "missing category/cents table"
        msg = "Markdown"
        raise InputError(msg, message)
    rows: list[tuple[str, int]] = []
    for line in lines[10:]:
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) != _MARKDOWN_CELL_COUNT or cells[0] or cells[3]:
            message = "malformed table row"
            msg = "Markdown"
            raise InputError(msg, message)
        rows.append((cells[1], int(cells[2])))
    return tuple(lines[:8]), tuple(rows)


def evaluate(artifact: Artifact, target: Requirements, context: Context) -> Check:
    """Check source provenance and actual bytes independently of policy contracts."""
    try:
        content = artifact.path.read_bytes()
    except OSError as error:
        return Check(Validity.UNKNOWN, f"artifact bytes unavailable: {error}")
    if digest(content) != artifact.sha256:
        return Check(Validity.INVALID, "artifact content digest mismatch")
    if (
        artifact.source_sha256 != context.source_sha256
        or artifact.code_sha256 != context.code_sha256
        or artifact.environment_sha256 != context.environment_sha256
        or artifact.contract_version != context.contract_version
    ):
        return Check(Validity.INVALID, "source/code/environment/contract provenance mismatch")
    try:
        oracle = source_oracle(target, context)
        match artifact.task:
            case Task.LOAD | Task.NORMALIZE | Task.AGGREGATE:
                valid = canonical(decode_json(content.decode("utf-8"))) == oracle.content(
                    artifact.task
                )
            case Task.RENDER:
                text = content.decode("utf-8")
                if target.output_format == "html":
                    actual, expected = _HtmlTokens(), _HtmlTokens()
                    actual.feed(text)
                    actual.close()
                    expected.feed(_html_expected(target, context, oracle))
                    expected.close()
                    valid = actual.tokens == expected.tokens
                else:
                    fields, rows = _markdown_fields(text)
                    expected_fields = (
                        f"# {target.title}",
                        *(f"{key}: {value}" for key, value in _metadata(target, context)),
                    )
                    valid = (
                        target.output_format == "markdown"
                        and fields == expected_fields
                        and rows == oracle.totals
                    )
            case unreachable:
                assert_never(unreachable)
    except (InputError, ValueError, UnicodeError, csv.Error) as error:
        return Check(Validity.INVALID, f"independent content parse failed: {error}")
    return Check(
        Validity.VALID if valid else Validity.INVALID,
        "source-derived role content matches" if valid else "source-derived role content mismatch",
    )
