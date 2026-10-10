"""Actual SELECT, SUMMARY and Markdown rendering with stage dependency fingerprints."""

from __future__ import annotations

import inspect
import platform
from pathlib import Path
from typing import assert_never

from src.intent_revalidation.fixtures import field, mapping, sequence, string
from src.intent_revalidation.model import InputError, Json, canonical, decode_json, digest
from src.intent_revalidation.policies import Policy

from .inputs import boolean, count
from .model import Column, Context, ReportRequirements, Source, Step


def make_context(source: Source) -> Context:
    root = Path(__file__).parent
    shared = b"".join(
        (root / name).read_bytes() for name in ("model.py", "inputs.py", "storage.py")
    )
    shared += (root.parent / "model.py").read_bytes() + (root.parent / "fixtures.py").read_bytes()
    shared += inspect.getsource(Policy).encode()
    functions = (select_rows, summarize, render)
    fingerprints = tuple(
        digest(shared + inspect.getsource(function).encode()) for function in functions
    )
    environment = canonical(
        {
            "python": platform.python_version(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        }
    )
    return Context(source, fingerprints, digest(environment), "report-workflow-v1")


def select_rows(requirements: ReportRequirements, context: Context) -> bytes:
    available = {row.case_id for row in context.source.rows}
    if not set(requirements.case_ids) <= available:
        raise InputError("case_ids", "requested case absent from source")
    return canonical(
        {
            "source_sha256": context.source.sha256,
            "case_ids": list(requirements.case_ids),
            "rows": [
                row.to_json() for row in context.source.rows if row.case_id in requirements.case_ids
            ],
        }
    )


def summarize(content: bytes) -> bytes:
    selected = mapping(decode_json(content.decode()))
    rows = [mapping(value) for value in sequence(field(selected, "rows"))]
    totals: list[Json] = []
    for policy in Policy:
        group = [row for row in rows if string(field(row, "policy")) == policy.value]
        totals.append(
            {
                "policy": policy.value,
                "valid_cases": sum(boolean(field(row, "valid")) for row in group),
                "total_cases": len(group),
                "executions": sum(count(field(row, "executions")) for row in group),
                "invalid_reuse": sum(count(field(row, "invalid_reuse")) for row in group),
            }
        )
    return canonical(
        {
            "source_sha256": field(selected, "source_sha256"),
            "case_ids": field(selected, "case_ids"),
            "rows": totals,
        }
    )


def render(content: bytes, requirements: ReportRequirements) -> bytes:
    summary = mapping(decode_json(content.decode()))
    lines = [
        f"# {requirements.title}",
        "",
        f"Source SHA256: {string(field(summary, 'source_sha256'))}",
        "Cases: " + ", ".join(string(item) for item in sequence(field(summary, "case_ids"))),
        "",
        "| " + " | ".join(requirements.columns) + " |",
        "| " + " | ".join("---" for _ in requirements.columns) + " |",
    ]
    for value in sequence(field(summary, "rows")):
        row = mapping(value)
        cells: list[str] = []
        for column in requirements.columns:
            match column:
                case Column.POLICY:
                    cells.append(string(field(row, "policy")))
                case Column.VALID_CASES:
                    cells.append(
                        f"{count(field(row, 'valid_cases'))}/{count(field(row, 'total_cases'))}"
                    )
                case Column.EXECUTIONS | Column.INVALID_REUSE:
                    cells.append(str(count(field(row, column.value))))
                case unreachable:
                    assert_never(unreachable)
        lines.append("| " + " | ".join(cells) + " |")
    return ("\n".join(lines) + "\n").encode()


def expected_content(step: Step, requirements: ReportRequirements, context: Context) -> bytes:
    selected = select_rows(requirements, context)
    match step:
        case Step.SELECT:
            return selected
        case Step.SUMMARY:
            return summarize(selected)
        case Step.RENDER:
            return render(summarize(selected), requirements)
        case unreachable:
            assert_never(unreachable)
