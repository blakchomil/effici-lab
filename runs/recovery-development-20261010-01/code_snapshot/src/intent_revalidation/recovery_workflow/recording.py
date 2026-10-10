"""Immutable inputs, executable source snapshots and point-in-time cache evidence."""

from __future__ import annotations

import platform
from pathlib import Path
from typing import TYPE_CHECKING

from src.intent_revalidation.model import Json, canonical, digest

from .scenarios import events

if TYPE_CHECKING:
    from src.intent_revalidation.report_workflow.cache import Result
    from src.intent_revalidation.report_workflow.model import Artifact, Context


def write_json(path: Path, value: Json) -> None:
    with path.open("xb") as stream:
        _ = stream.write(canonical(value))


def snapshot_cache(path: Path, cache: tuple[Artifact, ...]) -> None:
    snapshots: list[Json] = []
    for item in cache:
        actual_hash = digest(item.path.read_bytes()) if item.path.is_file() else None
        snapshots.append(
            {
                "artifact": item.to_json(),
                "present": actual_hash is not None,
                "actual_sha256": actual_hash,
                "hash_valid": actual_hash == item.sha256,
            }
        )
    write_json(path, snapshots)


def snapshot_result(path: Path, result: Result) -> None:
    path.mkdir()
    for item in result.artifacts:
        with (path / item.path.name).open("xb") as stream:
            _ = stream.write(item.path.read_bytes())
    write_json(path / "artifacts.json", [item.to_json() for item in result.artifacts])


def write_manifest(root: Path, context: Context, command: str) -> None:
    project = Path(__file__).resolve().parents[3]
    hashes: dict[str, Json] = {}
    for path in sorted((project / "src").rglob("*.py")):
        relative = path.relative_to(project)
        destination = root / "code_snapshot" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        content = path.read_bytes()
        with destination.open("xb") as stream:
            _ = stream.write(content)
        hashes[str(relative)] = digest(content)
    write_json(
        root / "manifest.json",
        {
            "study": "bounded-between-revision-recovery",
            "command": command,
            "source_sha256": context.source.sha256,
            "protocol_sha256": digest((root / "protocol.md").read_bytes()),
            "code_files": hashes,
            "code_sha256": digest(canonical(hashes)),
            "stage_code_hashes": list(context.fingerprints),
            "environment_sha256": context.env_hash,
            "environment": {
                "python": platform.python_version(),
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
            },
            "contract_version": context.contract_version,
            "events": [event.to_json() for event in events(context)],
            "case_origin": "public synthetic fault trace; not observed user incidents",
            "source_origin": "unchanged actual Phase 1 metrics; source experiment not re-executed",
            "held_out": False,
            "model_policy_evaluated": False,
            "process_isolation": False,
            "restart_recovery_evaluated": False,
            "policy_orders": [["B0", "B1", "B2"], ["B1", "B2", "B0"], ["B2", "B0", "B1"]],
            "initial_cache": "two actual B0 runs S0/S1; one seed, nine independent clones",
            "history": "each arm retains its own evolving cache; fault targets follow shared rules",
            "timings": "wall excludes faults/preparation/evaluation; internal times overlap",
            "cost_model": "unit new-stage count; not a time or dollar optimum",
        },
    )
