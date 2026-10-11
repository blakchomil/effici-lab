"""Observe Claude lifecycle and enforce a deliberately bounded publication gate."""

from __future__ import annotations

import argparse
import fcntl
import re
import shlex
import sys
import time
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Final

from src.intent_revalidation.fixtures import field, mapping, string
from src.intent_revalidation.model import InputError, Json, JsonObject, canonical, decode_json

from .evaluation import (
    control_files_intact,
    original_files_intact,
    read_text,
    valid_receipt,
    valid_report,
)
from .fixtures import RULES

PUBLISH_ARG_COUNT: Final = 3


class Arguments(argparse.Namespace):
    """Typed paths and arm selection at the command-line boundary."""

    workspace: Path = Path()
    events: Path = Path()
    arm: str = "G0"


@dataclass(frozen=True, slots=True)
class HookEvent:
    """Parsed hook input, retaining the original JSON for provenance."""

    name: str
    payload: JsonObject
    tool: str
    tool_input: JsonObject


def parse_event(raw: str) -> HookEvent:
    """Require event/tool fields before making an enforcement decision."""
    payload = mapping(decode_json(raw))
    name = string(field(payload, "hook_event_name"))
    if name not in {
        "SessionStart",
        "SessionEnd",
        "PreCompact",
        "SubagentStart",
        "SubagentStop",
        "PreToolUse",
        "PostToolUse",
        "PostToolUseFailure",
        "Stop",
    }:
        raise InputError("hook_event_name", "unsupported event")
    tool = ""
    tool_input: JsonObject = {}
    if name in {"PreToolUse", "PostToolUse", "PostToolUseFailure"}:
        tool = string(field(payload, "tool_name"))
        tool_input = mapping(field(payload, "tool_input"))
        if tool in {"Write", "Edit"}:
            _ = string(field(tool_input, "file_path"))
        if tool == "Bash":
            _ = string(field(tool_input, "command"))
    return HookEvent(name, payload, tool, tool_input)


def _publication_error(workspace: Path, phase: str) -> str:
    report = read_text(workspace / "out" / f"{phase}.json")
    receipt = read_text(workspace / "receipts" / f"{phase}.json")
    if not original_files_intact(workspace):
        return "Original source or protected fixture changed."
    if not valid_report(report):
        return "Report must satisfy gov-v1 before publication."
    if not valid_receipt(receipt, report, phase):
        return "Run python3 tools/verify_report.py for the current report before publication."
    return ""


def gate_reason(workspace: Path, event: HookEvent) -> str:
    """Cover Write/Edit paths and simple publisher commands, not arbitrary shell semantics."""
    if event.tool in {"Write", "Edit"}:
        path = Path(string(event.tool_input["file_path"]))
        destination = (workspace / path).resolve()
        if destination == (workspace / "protected.txt").resolve():
            return "protected.txt must remain byte-for-byte unchanged."
        if destination.parent == (workspace / "published").resolve():
            return _publication_error(workspace, destination.stem) or (
                "Publish through python3 tools/publish.py; direct publication writes are forbidden."
            )
    if event.tool == "Bash":
        try:
            words = shlex.split(string(event.tool_input["command"]))
        except ValueError:
            return "Malformed shell command cannot be checked by this bounded gate."
        if len(words) == PUBLISH_ARG_COUNT and words[0] in {"python", "python3"}:
            script = (workspace / words[1]).resolve()
            if script == (workspace / "tools/publish.py").resolve():
                phase = words[2]
                if re.fullmatch(r"[a-z][a-z0-9_-]*", phase) is None:
                    return "Invalid publication phase."
                return _publication_error(workspace, phase)
    return ""


def _artifacts(workspace: Path, folder: str) -> JsonObject:
    artifacts: dict[str, Json] = {}
    for path in sorted((workspace / folder).glob("*.json")):
        artifacts[path.stem] = {
            "content": read_text(path),
            "receipt": read_text(workspace / "receipts" / path.name),
        }
    return artifacts


def _snapshot(workspace: Path, events: Path) -> JsonObject:
    return {
        "publications": _artifacts(workspace, "published"),
        "reports": _artifacts(workspace, "out"),
        "originals_intact": original_files_intact(workspace),
        "controls_intact": control_files_intact(workspace, events),
    }


def _append(path: Path, record: JsonObject) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record["observed_monotonic_ns"] = time.monotonic_ns()
    with path.open("ab") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        _ = stream.write(canonical(record))
        stream.flush()
        fcntl.flock(stream, fcntl.LOCK_UN)


def process(workspace: Path, events: Path, arm: str, raw: str) -> tuple[int, JsonObject, str]:
    """Return hook exit code, JSON response and stderr while recording actual input."""
    try:
        event = parse_event(raw)
    except (InputError, JSONDecodeError) as error:
        _append(events, {"kind": "invalid_input", "arm": arm, "error": str(error), "raw": raw})
        return (2 if arm == "G2" else 0), {}, f"Invalid governance hook input: {error}\n"
    reason = gate_reason(workspace, event) if arm == "G2" and event.name == "PreToolUse" else ""
    record: JsonObject = {"kind": "hook", "arm": arm, "payload": event.payload}
    response: JsonObject = {}
    if event.name in {"PreToolUse", "PostToolUse", "PostToolUseFailure"}:
        record["snapshot"] = _snapshot(workspace, events)
    if event.name == "PreToolUse":
        record["gate_decision"] = "deny" if reason else "observe" if arm != "G2" else "allow"
        record["gate_reason"] = reason
    if reason:
        response = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
    if arm in {"G1", "G2"} and event.name in {"SessionStart", "SubagentStart"}:
        response = {
            "hookSpecificOutput": {
                "hookEventName": event.name,
                "additionalContext": RULES,
            }
        }
        record["injected_context"] = RULES
    _append(events, record)
    return 0, response, ""


def main() -> int:
    """Serve one Claude hook invocation using the existing stdlib CLI convention."""
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--workspace", type=Path, required=True)
    _ = parser.add_argument("--events", type=Path, required=True)
    _ = parser.add_argument("--arm", choices=("G0", "G1", "G2"), required=True)
    args = Arguments()
    _ = parser.parse_args(namespace=args)
    code, response, error = process(args.workspace, args.events, args.arm, sys.stdin.read())
    if response:
        _ = sys.stdout.write(canonical(response).decode())
    if error:
        _ = sys.stderr.write(error)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
