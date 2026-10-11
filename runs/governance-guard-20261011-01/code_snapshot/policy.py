"""Confined policy loading and content fingerprints."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from src.intent_revalidation.fixtures import field, mapping, sequence, string
from src.intent_revalidation.model import InputError, JsonObject, canonical, decode_json


def confined(root: Path, name: str) -> Path:
    """Resolve a project path, rejecting lexical traversal and symlink escapes."""
    candidate = Path(name)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise InputError(name, "expected a project-relative path without traversal")
    resolved = (root / candidate).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise InputError(name, "path escapes project root")
    return resolved


def strings(record: JsonObject, key: str) -> tuple[str, ...]:
    """Parse a nonempty string list."""
    values = tuple(string(item) for item in sequence(field(record, key)))
    if any(not item for item in values):
        raise InputError(key, "empty strings are forbidden")
    return values


@dataclass(frozen=True, slots=True)
class Policy:
    """Human configured policy; its complete JSON participates in freshness."""

    root: Path
    raw: JsonObject
    instructions: tuple[str, ...]
    tracked: tuple[str, ...]
    command: tuple[str, ...]
    gates: tuple[tuple[str, ...], ...]
    protected: tuple[str, ...]


def load(root: Path) -> Policy:
    """Read and validate the current on-disk policy."""
    root = root.resolve()
    raw = mapping(decode_json(confined(root, ".governance/policy.json").read_text()))
    if raw.get("schema") != "governance-guard-v1":
        raise InputError("schema", "unsupported policy schema")
    instructions = strings(raw, "instructions")
    tracked = strings(raw, "tracked")
    command = strings(raw, "check_argv")
    protected = strings(raw, "protected")
    gates = tuple(
        tuple(string(arg) for arg in sequence(gate)) for gate in sequence(field(raw, "gates"))
    )
    if not instructions or not command or any(not gate or not all(gate) for gate in gates):
        raise InputError("policy", "instructions, check argv and gate argv must be nonempty")
    for name in (*instructions, *tracked, *protected):
        _ = confined(root, name)
    return Policy(root, raw, instructions, tracked, command, gates, protected)


def snapshot(policy: Policy) -> JsonObject:
    """Hash instructions and tracked bytes including additions/deletions."""
    files: dict[str, str] = {}
    names = set(policy.instructions)
    for pattern in policy.tracked:
        for path in policy.root.glob(pattern):
            if path.is_file():
                name = path.relative_to(policy.root).as_posix()
                if not name.startswith(".governance/"):
                    names.add(name)
    for name in sorted(names):
        files[name] = hashlib.sha256(confined(policy.root, name).read_bytes()).hexdigest()
    hashes: JsonObject = dict(files)
    return {
        "policy_hash": hashlib.sha256(canonical(policy.raw)).hexdigest(),
        "sources": hashes,
    }


def context(policy: Policy) -> str:
    """Return actual instructions and the current content fingerprint."""
    sections = [
        "Governance Guard: checks prove configured checks only; obey current instructions.",
        canonical({"policy": policy.raw, "snapshot": snapshot(policy)}).decode(),
    ]
    sections.extend(
        f"\n--- {name} ---\n{confined(policy.root, name).read_text()}"
        for name in policy.instructions
    )
    return "\n".join(sections)
