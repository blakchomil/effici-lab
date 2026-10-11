"""Command-line interface for opt-in, project-local governance checks."""

from __future__ import annotations

import argparse
import shlex
import sys
from json import JSONDecodeError
from pathlib import Path

from src.intent_revalidation.fixtures import mapping
from src.intent_revalidation.model import InputError, JsonObject, canonical, decode_json

from .hooks import decision, deny
from .policy import confined, context, load
from .receipts import check, status


class Arguments(argparse.Namespace):
    """Typed argparse boundary matching the repository's dependency-free CLI."""

    action: str = ""
    root: Path = Path()
    instructions: list[str] | None = None
    track: list[str] | None = None
    check: str = ""
    gate: list[str] | None = None
    protect: list[str] | None = None
    timeout: float = 60


def initialize(args: Arguments) -> JsonObject:
    """Create policy exclusively; generate opt-in session hook settings."""
    root = args.root.resolve(strict=True)
    instructions = args.instructions or ["CLAUDE.md"]
    tracked = args.track or []
    protected = args.protect or []
    command = shlex.split(args.check)
    gates = [shlex.split(item) for item in args.gate or []]
    if not command or any(not gate for gate in gates):
        raise InputError("command", "check and gate commands must contain argv")
    for name in (*instructions, *tracked, *protected):
        _ = confined(root, name)
    for name in instructions:
        _ = confined(root, name).read_text()
    raw: JsonObject = {
        "schema": "governance-guard-v1",
        "version": 1,
        "instructions": list(instructions),
        "tracked": list(tracked),
        "check_argv": list(command),
        "gates": [list(gate) for gate in gates],
        "protected": list(protected),
    }
    folder = confined(root, ".governance")
    folder.mkdir(exist_ok=True)
    policy_path = confined(root, ".governance/policy.json")
    with policy_path.open("x") as handle:
        _ = handle.write(canonical(raw).decode() + "\n")
    repository = Path(__file__).resolve().parents[3]
    hook_command = (
        f"cd {shlex.quote(str(repository))} && "
        f"{shlex.quote(sys.executable)} -m src.intent_revalidation.governance_guard "
        f"hook --root {shlex.quote(str(root))}"
    )
    hooks: JsonObject = {}
    for event in ("SessionStart", "SubagentStart", "PreToolUse"):
        hooks[event] = [
            {
                "matcher": "Bash|Write|Edit" if event == "PreToolUse" else "",
                "hooks": [{"type": "command", "command": hook_command}],
            }
        ]
    settings: JsonObject = {"hooks": hooks}
    settings_path = confined(root, ".governance/session-settings.json")
    with settings_path.open("x") as handle:
        _ = handle.write(canonical(settings).decode() + "\n")
    return {
        "policy_path": str(policy_path),
        "settings_path": str(settings_path),
        "settings": settings,
        "activated": False,
    }


def parser() -> argparse.ArgumentParser:
    """Expose initialization separately from runtime hooks and checks."""
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="action", required=True)
    for action in ("init", "context", "check", "status", "hook"):
        sub = subparsers.add_parser(action)
        _ = sub.add_argument("--root", type=Path, required=True)
        if action == "init":
            _ = sub.add_argument("--instructions", action="append")
            _ = sub.add_argument("--track", action="append")
            _ = sub.add_argument("--check", required=True)
            _ = sub.add_argument("--gate", action="append")
            _ = sub.add_argument("--protect", action="append")
        if action == "check":
            _ = sub.add_argument("--timeout", type=float, default=60)
    return result


def main() -> int:
    """Emit machine-readable results and fail closed on hook configuration errors."""
    args = parser().parse_args(namespace=Arguments())
    try:
        if args.action == "init":
            output = initialize(args)
        else:
            policy = load(args.root)
            if args.action == "context":
                _ = sys.stdout.write(context(policy) + "\n")
                return 0
            if args.action == "check":
                output = check(policy, args.timeout)
                _ = sys.stdout.write(canonical(output).decode() + "\n")
                return 0 if output["passed"] is True else 1
            if args.action == "status":
                output = status(policy)
            else:
                output = decision(policy, mapping(decode_json(sys.stdin.read())))
        _ = sys.stdout.write(canonical(output).decode() + "\n")
    except (OSError, InputError, JSONDecodeError, ValueError) as error:
        if args.action == "hook":
            _ = sys.stdout.write(canonical(deny(str(error))).decode() + "\n")
            return 0
        _ = sys.stderr.write(f"governance_guard: {error}\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
