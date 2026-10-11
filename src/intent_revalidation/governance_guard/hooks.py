"""Claude hook decisions for explicit command prefixes and protected paths."""

from __future__ import annotations

import re
import shlex
from pathlib import Path

from src.intent_revalidation.fixtures import field, mapping, string
from src.intent_revalidation.model import InputError, JsonObject

from .policy import Policy, confined, context
from .receipts import status


def deny(reason: str) -> JsonObject:
    """Encode a Claude PreToolUse denial."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def decision(policy: Policy, event: JsonObject) -> JsonObject:
    """Reinject context or inspect the deliberately limited tool surface."""
    name = string(field(event, "hook_event_name"))
    if name in {"SessionStart", "SubagentStart"}:
        return {"hookSpecificOutput": {"hookEventName": name, "additionalContext": context(policy)}}
    if name != "PreToolUse":
        raise InputError("hook_event_name", "unsupported hook event")
    tool = string(field(event, "tool_name"))
    payload = mapping(field(event, "tool_input"))
    if tool in {"Write", "Edit"}:
        path = Path(string(field(payload, "file_path")))
        if path.is_absolute():
            try:
                path = path.relative_to(policy.root)
            except ValueError:
                return deny("Write/Edit path is outside the configured project")
        target = confined(policy.root, str(path))
        protected = [confined(policy.root, item) for item in policy.protected]
        if target.is_relative_to(confined(policy.root, ".governance")) or target in protected:
            return deny("Protected governance or configured project path")
    if tool == "Bash":
        return bash_decision(policy, string(field(payload, "command")))
    return {}


def bash_decision(policy: Policy, command: str) -> JsonObject:
    """Reject visible compound gates; exact argv prefixes require a fresh check."""
    try:
        argv = shlex.split(command)
    except ValueError:
        return deny("Unparseable Bash command")
    direct = any(tuple(argv[: len(gate)]) == gate for gate in policy.gates)
    wrapped = any(
        tuple(argv[index : index + len(gate)]) == gate or shlex.join(gate) in command
        for gate in policy.gates
        for index in range(len(argv))
    )
    compound = bool(re.search(r"[;&|<>`$()\n]", command))
    visible = any(gate[0] in command for gate in policy.gates)
    if compound and visible:
        return deny("Run the configured gated command directly without shell expressions")
    if wrapped and not direct:
        return deny("Run the configured gated command directly without wrappers or assignments")
    if direct and status(policy)["valid"] is not True:
        return deny("Run governance_guard check for the current policy and tracked files")
    return {}
