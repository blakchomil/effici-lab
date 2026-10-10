"""Evaluator-only reconstruction from the original metrics, independent of stages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import assert_never

from src.intent_revalidation.model import (
    Check,
    InputError,
    Json,
    JsonObject,
    Validity,
    canonical,
    decode_json,
    digest,
)

from .model import Artifact, Context, ReportRequirements, Step


def _mapping(value: Json) -> JsonObject:
    match value:
        case dict() as result:
            return result
        case None | bool() | int() | float() | str() | list():
            raise InputError("oracle", "expected a JSON object")
        case unreachable:
            assert_never(unreachable)


def _integer(value: Json) -> int:
    match value:
        case bool():
            raise InputError("oracle", "boolean is not a count")
        case int() as result:
            if result < 0:
                raise InputError("oracle", "expected nonnegative count")
            return result
        case None | float() | str() | list() | dict():
            raise InputError("oracle", "expected an integer")
        case unreachable:
            assert_never(unreachable)


def _boolean(value: Json) -> bool:
    match value:
        case bool() as result:
            return result
        case None | int() | float() | str() | list() | dict():
            raise InputError("oracle", "final_satisfied must be boolean")
        case unreachable:
            assert_never(unreachable)


def _sequence(value: Json) -> list[Json]:
    match value:
        case list() as result:
            return result
        case None | bool() | int() | float() | str() | dict():
            raise InputError("oracle", "expected original metrics array")
        case unreachable:
            assert_never(unreachable)


def _text(value: Json) -> str:
    match value:
        case str() as result:
            return result
        case None | bool() | int() | float() | list() | dict():
            raise InputError("oracle", "missing case or policy")
        case unreachable:
            assert_never(unreachable)


@dataclass(frozen=True, slots=True)
class Oracle:
    """Source-derived canonical stage bytes and visible table expectations."""

    selected: bytes
    summary: bytes
    rows: tuple[tuple[str, ...], ...]

    def content(self, step: Step) -> bytes:
        match step:
            case Step.SELECT:
                return self.selected
            case Step.SUMMARY:
                return self.summary
            case Step.RENDER:
                raise InputError("oracle", "terminal report hash is unnecessary for planning")
            case unreachable:
                assert_never(unreachable)


def source_oracle(target: ReportRequirements, context: Context) -> Oracle:
    """Recompute evidence without trusting parsed Source.rows or policy helpers."""
    source_hash = digest(context.source.content)
    if source_hash != context.source.sha256:
        raise InputError("oracle", "source fingerprint mismatch")
    raw = _sequence(decode_json(context.source.content.decode("utf-8")))
    if not raw:
        raise InputError("oracle", "expected nonempty original metrics")
    selected: list[tuple[str, str, Json]] = []
    totals = {policy: [0, 0, 0, 0] for policy in ("B0", "B1", "B2")}
    seen: set[tuple[str, str]] = set()
    for value in raw:
        row = _mapping(value)
        case_id, policy = _text(row.get("case_id")), _text(row.get("policy"))
        if policy not in totals or (case_id, policy) in seen:
            raise InputError("oracle", "unsupported policy or duplicate case/policy")
        seen.add((case_id, policy))
        audit = _mapping(row.get("audit"))
        valid = _boolean(audit.get("final_satisfied"))
        executions = _integer(_mapping(row.get("operation_counts")).get("policy_executions", 0))
        invalid_reuse = _integer(audit.get("invalid_reuse_events"))
        if case_id in target.case_ids:
            selected.append(
                (
                    case_id,
                    policy,
                    {
                        "case_id": case_id,
                        "policy": policy,
                        "valid": valid,
                        "executions": executions,
                        "invalid_reuse": invalid_reuse,
                    },
                )
            )
            values = totals[policy]
            values[0] += int(valid)
            values[1] += 1
            values[2] += executions
            values[3] += invalid_reuse
    cases = {case_id for case_id, _ in seen}
    if seen != {(case_id, policy) for case_id in cases for policy in totals}:
        raise InputError("oracle", "unbalanced case/policy coverage")
    if not set(target.case_ids) <= cases:
        raise InputError("oracle", "selected case missing from original source")
    selected.sort(key=lambda item: item[:2])
    summary: list[Json] = []
    table: list[tuple[str, ...]] = []
    for policy, (valid, count, executions, invalid_reuse) in totals.items():
        summary.append(
            {
                "policy": policy,
                "valid_cases": valid,
                "total_cases": count,
                "executions": executions,
                "invalid_reuse": invalid_reuse,
            }
        )
        cells = {
            "policy": policy,
            "valid_cases": f"{valid}/{count}",
            "executions": str(executions),
            "invalid_reuse": str(invalid_reuse),
        }
        table.append(tuple(cells[column.value] for column in target.columns))
    base: JsonObject = {"source_sha256": source_hash, "case_ids": list(target.case_ids)}
    return Oracle(
        canonical({**base, "rows": [item[2] for item in selected]}),
        canonical({**base, "rows": summary}),
        tuple(table),
    )


def _report_matches(content: bytes, target: ReportRequirements, context: Context) -> bool:
    lines = [line.strip() for line in content.decode("utf-8").splitlines() if line.strip()]
    prefix = [
        f"# {target.title}",
        f"Source SHA256: {context.source.sha256}",
        f"Cases: {', '.join(target.case_ids)}",
    ]
    if lines[: len(prefix)] != prefix:
        return False
    parsed: list[tuple[str, ...]] = []
    for line in lines[len(prefix) :]:
        fields = tuple(cell.strip() for cell in line.split("|"))
        if len(fields) != len(target.columns) + 2 or fields[0] or fields[-1]:
            return False
        parsed.append(fields[1:-1])
    expected = (
        tuple(column.value for column in target.columns),
        tuple("---" for _ in target.columns),
        *source_oracle(target, context).rows,
    )
    return tuple(parsed) == expected


def evaluate(artifact: Artifact, target: ReportRequirements, context: Context) -> Check:
    """Validate actual content and provenance; auditors separately check actual bindings."""
    evidence = (
        artifact.sha256,
        artifact.input_hash,
        artifact.code_hash,
        artifact.env_hash,
        artifact.source_hash,
        artifact.contract_version,
        artifact.generation_revision,
    )
    if not all(evidence):
        return Check(Validity.UNKNOWN, "missing provenance evidence")
    try:
        content = artifact.path.read_bytes()
    except OSError as error:
        return Check(Validity.UNKNOWN, f"artifact bytes unavailable: {error}")
    if digest(content) != artifact.sha256:
        return Check(Validity.INVALID, "actual content fingerprint mismatch")
    if (
        artifact.source_hash != context.source.sha256
        or artifact.code_hash != context.code_hash(artifact.step)
        or artifact.env_hash != context.env_hash
        or artifact.contract_version != context.contract_version
    ):
        return Check(Validity.INVALID, "source/code/environment/contract provenance mismatch")
    try:
        oracle = source_oracle(target, context)
        match artifact.step:
            case Step.SELECT:
                valid = content == oracle.selected and artifact.input_hash == context.source.sha256
            case Step.SUMMARY:
                valid = content == oracle.summary and artifact.input_hash == digest(oracle.selected)
            case Step.RENDER:
                valid = _report_matches(content, target, context) and artifact.input_hash == digest(
                    oracle.summary
                )
            case unreachable:
                assert_never(unreachable)
    except (InputError, ValueError, UnicodeError) as error:
        return Check(Validity.INVALID, f"independent source/content parse failed: {error}")
    return Check(
        Validity.VALID if valid else Validity.INVALID,
        "source-derived content matches" if valid else "source-derived content mismatch",
    )
