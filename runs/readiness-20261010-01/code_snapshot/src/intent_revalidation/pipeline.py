"""Four deterministic operations and dependency-granular content cache keys."""

from __future__ import annotations

from html import escape
from typing import assert_never

from .content import (
    Aggregate,
    aggregate_content,
    records_content,
    snapshot,
    source_records,
    sum_records,
)
from .model import Artifact, Context, InputError, Requirements, Task, canonical, digest


def cache_key(
    task: Task, requirements: Requirements, context: Context, inputs: tuple[Artifact, ...]
) -> str:
    """Hash directly relevant requirements and actual input bytes, never revision IDs."""
    return digest(
        canonical(
            {
                "task": task.value,
                "requirements": requirements.relevant(task),
                "inputs": [digest(item.path.read_bytes()) for item in inputs],
                "source_sha256": digest(context.source),
                "code_sha256": context.code_sha256,
                "environment_sha256": context.environment_sha256,
                "contract_version": context.contract_version,
            }
        )
    )


def extension(task: Task, requirements: Requirements) -> str:
    """Return the real file extension for this output role."""
    match task:
        case Task.LOAD | Task.NORMALIZE | Task.AGGREGATE:
            return ".json"
        case Task.RENDER:
            if requirements.output_format == "markdown":
                return ".md"
            if requirements.output_format == "html":
                return ".html"
            raise InputError("output.format", "supported formats: markdown, html")
        case unreachable:
            assert_never(unreachable)


def _render(aggregate: Aggregate, requirements: Requirements) -> bytes:
    labels = aggregate.labels(requirements.language)
    if requirements.output_format == "markdown":
        lines = [f"# {requirements.title}", ""]
        lines.extend(f"{label}: {value}" for label, value in labels)
        lines.extend(["", "| category | amount_cents |", "| --- | ---: |"])
        lines.extend(f"| {category} | {amount} |" for category, amount in aggregate.totals)
        return ("\n".join(lines) + "\n").encode()
    if requirements.output_format != "html":
        raise InputError("output.format", "supported formats: markdown, html")
    title = escape(requirements.title)
    metadata = "".join(f"<dt>{escape(key)}</dt><dd>{escape(value)}</dd>" for key, value in labels)
    rows = "".join(
        f"<tr><td>{escape(category)}</td><td>{amount}</td></tr>"
        for category, amount in aggregate.totals
    )
    return (
        f'<!DOCTYPE html>\n<html lang="{escape(requirements.language, quote=True)}">'
        f'<head><meta charset="utf-8"/><title>{title}</title></head><body>'
        f"<h1>{title}</h1><dl>{metadata}</dl><table><thead><tr><th>category</th>"
        f"<th>amount_cents</th></tr></thead><tbody>{rows}</tbody></table></body></html>\n"
    ).encode()


def execute(
    task: Task, requirements: Requirements, context: Context, inputs: tuple[Artifact, ...]
) -> bytes:
    """Execute one role using its selected upstream content and fixed source snapshot."""
    if (
        requirements.dataset_id != context.dataset_id
        or digest(context.source) != context.source_sha256
    ):
        raise InputError("source", "dataset or source fingerprint differs from context")
    expected_count = 0 if task is Task.LOAD else 1
    if len(inputs) != expected_count:
        raise InputError("inputs", f"{task.value} expects {expected_count} inputs")
    match task:
        case Task.LOAD:
            return canonical(
                snapshot(context, [row.raw() for row in source_records(context.source)])
            )
        case Task.NORMALIZE:
            rows = records_content(inputs[0].path.read_bytes(), normalized=False)
            return canonical(snapshot(context, [row.normalized() for row in rows]))
        case Task.AGGREGATE:
            rows = records_content(inputs[0].path.read_bytes(), normalized=True)
            result = Aggregate(
                context.dataset_id,
                context.source_sha256,
                requirements.start,
                requirements.end,
                sum_records(rows, requirements),
            )
            return canonical(result.to_json())
        case Task.RENDER:
            return _render(aggregate_content(inputs[0].path.read_bytes()), requirements)
        case unreachable:
            assert_never(unreachable)
