"""Immutable source/config snapshots and explicitly unavailable subscription cost."""

from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, assert_never

from src.intent_revalidation.fixtures import mapping, string
from src.intent_revalidation.model import InputError, JsonObject, canonical, decode_json, digest
from src.intent_revalidation.recovery_workflow.recording import write_json

from .evaluation import read_events

if TYPE_CHECKING:
    from src.intent_revalidation.model import Json


def inspect_cli(executable: str) -> JsonObject:
    """Store auth method/status only; discard account identity and credential fields."""
    version = subprocess.run(  # noqa: S603 - fixed introspection command
        [executable, "--version"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    status = subprocess.run(  # noqa: S603 - read-only; account identity is not retained
        [executable, "auth", "status"],
        capture_output=True,
        text=True,
        check=True,
    )
    auth = mapping(decode_json(status.stdout))
    return {
        "version": version,
        "logged_in": auth.get("loggedIn"),
        "auth_method": auth.get("authMethod"),
        "provider": auth.get("apiProvider"),
        "subscription_type": auth.get("subscriptionType"),
        "cash_cost_usd": None,
    }


def manifest(root: Path, command: str, cli: JsonObject) -> None:
    """Snapshot executable code and fixed protocol before any comparative model call."""
    project = Path(__file__).resolve().parents[3]
    git = shutil.which("git")
    if git is None:
        raise InputError("git", "git metadata executable unavailable")
    hashes: dict[str, Json] = {}
    for source in sorted((project / "src").rglob("*.py")):
        relative = source.relative_to(project)
        target = root / "code_snapshot" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        _ = shutil.copyfile(source, target)
        hashes[str(relative)] = digest(source.read_bytes())
    _ = shutil.copyfile(project / "examples/governance/protocol-20261011.md", root / "protocol.md")
    payload: JsonObject = {
        "command": command,
        "cli": cli,
        "code_files": hashes,
        "code_sha256": digest(canonical(hashes)),
        "protocol_sha256": digest((root / "protocol.md").read_bytes()),
        "git_head": subprocess.run(  # noqa: S603 - resolved git, fixed read-only arguments
            [git, "rev-parse", "HEAD"],
            cwd=project,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip(),
        "git_status": list(
            subprocess.run(  # noqa: S603 - resolved git, fixed read-only arguments
                [git, "status", "--short"],
                cwd=project,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.splitlines()
        ),
        "environment": {
            "python": platform.python_version(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "held_out": False,
        "external_case": False,
        "case_origin": "public synthetic governance workload",
        "sampling": "one sequential initial/compact/restart/delegation trajectory per arm",
        "subscription_cash_cost_usd": None,
        "existing_global_instruction_loading_excluded": False,
    }
    write_json(root / "manifest.json", payload)


def returned_results(root: Path) -> list[Json]:
    """Retain returned usage exactly; do not infer incremental subscription cash charges."""
    results: list[Json] = []
    for path in sorted(root.glob("*.stdout.jsonl")):
        for line in path.read_text().splitlines(keepends=True):
            if not line.endswith("\n"):
                continue
            value = mapping(decode_json(line))
            if value.get("type") == "result":
                results.append(value)
    return results


def _tool_names(value: JsonObject) -> tuple[str, ...]:
    match value.get("message"):
        case dict() as message:
            match message.get("content"):
                case list() as blocks:
                    return tuple(
                        string(block["name"])
                        for block in blocks
                        if isinstance(block, dict)
                        and block.get("type") == "tool_use"
                        and isinstance(block.get("name"), str)
                    )
                case None | str() | bool() | int() | float() | dict():
                    return ()
                case unreachable:
                    assert_never(unreachable)
        case None | str() | bool() | int() | float() | list():
            return ()
        case unreachable:
            assert_never(unreachable)


def transcript_evidence(root: Path, events: Path) -> JsonObject:
    """Capture only transcripts named by this trial's lifecycle hook receipts."""
    private = root / "private"
    private.mkdir(exist_ok=True)
    snapshots: list[Json] = []
    compact_boundary = False
    agent_call = False
    child_transcript = False
    paths: dict[str, bool] = {}
    for record in read_events(events):
        payload = mapping(record.get("payload", {}))
        for field in ("transcript_path", "agent_transcript_path"):
            value = payload.get(field)
            match value:
                case str() as filename:
                    paths[filename] = paths.get(filename, False) or field == "agent_transcript_path"
                case None | bool() | int() | float() | dict() | list():
                    continue
                case unreachable:
                    assert_never(unreachable)
    for filename in sorted(paths):
        source = Path(filename)
        if not source.is_file():
            continue
        content = source.read_bytes()
        destination = private / (digest(filename.encode())[:12] + ".jsonl")
        _ = destination.write_bytes(content)
        snapshots.append(
            {
                "source": filename,
                "snapshot": str(destination.relative_to(root)),
                "sha256": digest(content),
            }
        )
        for line in content.decode().splitlines():
            value = mapping(decode_json(line))
            compact_boundary |= value.get("subtype") == "compact_boundary"
            child_transcript |= paths[filename] and value.get("isSidechain") is True
            agent_call |= (
                not paths[filename]
                and value.get("isSidechain") is not True
                and any(name in {"Agent", "Task"} for name in _tool_names(value))
            )
    return {
        "snapshots": snapshots,
        "compact_boundary": compact_boundary,
        "parent_agent_tool_call": agent_call,
        "child_transcript": child_transcript,
    }
