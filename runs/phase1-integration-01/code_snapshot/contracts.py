"""Executable role checks independent of pipeline execution and cache keys."""

from __future__ import annotations

from html.parser import HTMLParser
from typing import assert_never, override

from .content import Aggregate, iso_date, json_content, snapshot, source_records
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
    digest,
)


def _expected_aggregate(target: Requirements, context: Context) -> Aggregate:
    totals: dict[str, int] = {}
    for row in source_records(context.source):
        day = iso_date(row.day)
        if target.start <= day < target.end:
            totals[row.category] = totals.get(row.category, 0) + int(row.amount)
    return Aggregate(
        context.dataset_id,
        context.source_sha256,
        target.start,
        target.end,
        tuple(sorted(totals.items())),
    )


class _HTMLTokens(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tokens: list[str] = []

    @override
    def handle_decl(self, decl: str) -> None:
        self.tokens.append(f"declaration:{decl.lower()}")

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tokens.append(f"start:{tag}:{sorted(attrs)!r}")

    @override
    def handle_endtag(self, tag: str) -> None:
        self.tokens.append(f"end:{tag}")

    @override
    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    @override
    def handle_data(self, data: str) -> None:
        if data.strip():
            self.tokens.append(f"text:{data}")

    @override
    def handle_comment(self, data: str) -> None:
        self.tokens.append(f"comment:{data}")

    @override
    def handle_pi(self, data: str) -> None:
        self.tokens.append(f"instruction:{data}")


def _leaf(tag: str, value: str) -> list[str]:
    return [f"start:{tag}:[]", f"text:{value}", f"end:{tag}"]


def _html_matches(text: str, target: Requirements, expected: Aggregate) -> bool:
    parser = _HTMLTokens()
    parser.feed(text)
    parser.close()
    tokens = [
        "declaration:doctype html",
        f"start:html:{[('lang', target.language)]!r}",
        "start:head:[]",
        "start:meta:[('charset', 'utf-8')]",
    ]
    tokens.extend(_leaf("title", target.title))
    tokens.extend(["end:head", "start:body:[]"])
    tokens.extend(_leaf("h1", target.title))
    tokens.append("start:dl:[]")
    for label, value in expected.labels(target.language):
        tokens.extend(_leaf("dt", label))
        tokens.extend(_leaf("dd", value))
    tokens.extend(["end:dl", "start:table:[]", "start:thead:[]", "start:tr:[]"])
    tokens.extend(_leaf("th", "category"))
    tokens.extend(_leaf("th", "amount_cents"))
    tokens.extend(["end:tr", "end:thead", "start:tbody:[]"])
    for category, amount in expected.totals:
        tokens.append("start:tr:[]")
        tokens.extend(_leaf("td", category))
        tokens.extend(_leaf("td", str(amount)))
        tokens.append("end:tr")
    tokens.extend(["end:tbody", "end:table", "end:body", "end:html"])
    return parser.tokens == tokens


def _report_matches(content: bytes, target: Requirements, expected: Aggregate) -> bool:
    text = content.decode("utf-8")
    if target.output_format == "html":
        return _html_matches(text, target, expected)
    if target.output_format != "markdown":
        return False
    lines = text.splitlines()
    header = [f"# {target.title}", ""]
    header.extend(f"{label}: {value}" for label, value in expected.labels(target.language))
    header.extend(["", "| category | amount_cents |", "| --- | ---: |"])
    table = [f"| {category} | {amount} |" for category, amount in expected.totals]
    return lines == header + table


def _content_matches(artifact: Artifact, target: Requirements, context: Context) -> bool:
    content = artifact.path.read_bytes()
    match artifact.task:
        case Task.LOAD:
            expected: Json = snapshot(
                context, [row.raw() for row in source_records(context.source)]
            )
        case Task.NORMALIZE:
            expected = snapshot(
                context, [row.normalized() for row in source_records(context.source)]
            )
        case Task.AGGREGATE:
            expected = _expected_aggregate(target, context).to_json()
        case Task.RENDER:
            return _report_matches(content, target, _expected_aggregate(target, context))
        case unreachable:
            assert_never(unreachable)
    return canonical(json_content(content)) == canonical(expected)


def _metadata_error(artifact: Artifact, context: Context) -> str | None:
    if digest(artifact.path.read_bytes()) != artifact.sha256:
        return "artifact bytes differ from recorded digest"
    fingerprints = (
        ("source", artifact.source_sha256, context.source_sha256),
        ("code", artifact.code_sha256, context.code_sha256),
        ("environment", artifact.environment_sha256, context.environment_sha256),
        ("contract", artifact.contract_version, context.contract_version),
    )
    for name, actual, expected in fingerprints:
        if actual != expected:
            return f"{name} differs from current context"
    if artifact.requirements.dataset_id != context.dataset_id:
        return "artifact dataset differs from source context"
    return None


def _input_error(
    artifact: Artifact, target: Requirements, context: Context, inputs: tuple[Artifact, ...]
) -> str | None:
    count = 0 if artifact.task is Task.LOAD else 1
    if len(inputs) != count or len(artifact.input_ids) != count:
        return "selected input arity differs from role"
    if artifact.input_hashes != tuple(digest(item.path.read_bytes()) for item in inputs):
        return "selected input bytes differ from recorded linkage"
    upstream = {
        Task.NORMALIZE: Task.LOAD,
        Task.AGGREGATE: Task.NORMALIZE,
        Task.RENDER: Task.AGGREGATE,
    }
    for item in inputs:
        if item.task is not upstream[artifact.task]:
            return "selected input has wrong role"
        error = _metadata_error(item, context)
        if error:
            return f"input: {error}"
        if not _content_matches(item, target, context):
            return "selected input violates current role content"
    return None


def _contract_error(
    artifact: Artifact, target: Requirements, context: Context, inputs: tuple[Artifact, ...]
) -> str | None:
    if target.dataset_id != context.dataset_id or digest(context.source) != context.source_sha256:
        return "target dataset or source fingerprint differs from context"
    error = _metadata_error(artifact, context)
    if error:
        return error
    if artifact.requirements.relevant(artifact.task) != target.relevant(artifact.task):
        return "generation requirements differ for this role"
    error = _input_error(artifact, target, context, inputs)
    if error:
        return error
    if not _content_matches(artifact, target, context):
        return "artifact content violates current role contract"
    return None


def check_artifact(
    artifact: Artifact, target: Requirements, context: Context, inputs: tuple[Artifact, ...]
) -> Check:
    """Validate bytes, context, selected-input linkage and the complete consumer role."""
    try:
        error = _contract_error(artifact, target, context, inputs)
        if error:
            return Check(Validity.INVALID, error)
    except OSError as exc:
        return Check(Validity.UNKNOWN, f"artifact evidence unavailable: {exc}")
    except (InputError, UnicodeDecodeError, ValueError) as exc:
        return Check(Validity.INVALID, f"malformed role content: {exc}")
    return Check(Validity.VALID, "byte integrity, context, input linkage and role content match")
