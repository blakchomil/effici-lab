"""Three real Claude trajectories, with missing lifecycle trials explicitly unevaluated."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Final
from uuid import uuid4

from src.intent_revalidation.fixtures import mapping, sequence, string
from src.intent_revalidation.model import InputError, Json, JsonObject
from src.intent_revalidation.recovery_workflow.recording import write_json

from .evaluation import evaluate_phase, lifecycle_evidence, read_events
from .fixtures import prepare_workspace
from .processes import Session, headless
from .recording import inspect_cli, manifest, returned_results, transcript_evidence
from .reporting import write_report
from .stream import continuous, prompt

if TYPE_CHECKING:
    from collections.abc import Callable

PHASES: Final = ("initial", "compact", "restart", "delegation")
ARMS: Final = ("G0", "G1", "G2")


def eligibility(phase: str, evidence: JsonObject) -> bool:
    """A valid artifact cannot replace missing proof of the claimed transition."""
    checks = {
        "initial": evidence.get("startup") is True,
        "compact": evidence.get("manual_precompact") is True
        and evidence.get("compact_sessionstart") is True,
        "restart": evidence.get("new_pid") is True and evidence.get("same_resumed_uuid") is True,
        "delegation": evidence.get("parent_agent_tool_call") is True
        and evidence.get("matching_child_lifecycle") is True
        and evidence.get("child_transcript") is True,
    }
    if phase not in checks:
        raise InputError("phase", "unknown lifecycle phase")
    return checks[phase]


def transition_evidence(session: Session, processes: list[Json]) -> tuple[JsonObject, JsonObject]:
    """Collect lifecycle receipts independently of task completion and final artifacts."""
    events = session.evidence / "events.jsonl"
    life = lifecycle_evidence(events)
    payloads = [mapping(event.get("payload", {})) for event in read_events(events)]
    starts = sequence(life.get("subagent_start_ids", []))
    stops = sequence(life.get("subagent_stop_ids", []))
    first = mapping(processes[0]) if processes else {}
    restarted = mapping(processes[1]) if len(processes) > 1 else {}
    transition: JsonObject = {
        "startup": session.session_id in sequence(life.get("startup_session_ids", [])),
        "manual_precompact": any(
            event.get("hook_event_name") == "PreCompact" and event.get("trigger") == "manual"
            for event in payloads
        ),
        "compact_sessionstart": life.get("compact_sessionstart_observed"),
        "new_pid": bool(restarted)
        and first.get("pid") is not None
        and restarted.get("pid") is not None
        and first.get("pid") != restarted.get("pid")
        and first.get("returncode") is not None,
        "same_resumed_uuid": restarted.get("session_id") == session.session_id
        and session.session_id in sequence(life.get("resume_session_ids", [])),
        "matching_child_lifecycle": any(item is not None and item in stops for item in starts),
        **transcript_evidence(session.evidence, events),
    }
    return transition, life


def _resume_phases(
    session: Session, capture: Callable[[str], None]
) -> tuple[list[Json], JsonObject]:
    processes: list[Json] = []
    errors: JsonObject = {}
    for phase in ("restart", "delegation"):
        process = headless(session, phase, prompt(phase, delegate=phase == "delegation"))
        processes.append(process)
        if process.get("returncode") == 0 and process.get("timed_out") is False:
            capture(phase)
        else:
            errors[phase] = f"{phase} process failed: {process}"
            break
    return processes, errors


def run_arm(arm: str, session: Session, blocked: str | None) -> tuple[list[Json], JsonObject]:
    """Record one evolving session while attributing each runtime error to its phase."""
    events = session.evidence / "events.jsonl"
    audits: JsonObject = {}
    processes: list[Json] = []
    errors: JsonObject = dict.fromkeys(PHASES, blocked) if blocked else {}

    def capture(phase: str) -> None:
        audit = evaluate_phase(session.workspace, phase, events).to_json()
        audits[phase] = audit
        write_json(session.evidence / f"{phase}.audit.json", audit)

    auth_block = blocked
    if blocked is None:
        initial = continuous(session, events, capture)
        processes.append(initial)
        runtime_error = initial.get("error")
        if runtime_error is not None:
            failure = string(runtime_error)
            errors["compact" if "initial" in audits else "initial"] = failure
            if "authenticate" in failure or "OAuth" in failure:
                auth_block = failure
        else:
            resumed, failures = _resume_phases(session, capture)
            processes.extend(resumed)
            errors.update(failures)
    transition, life = transition_evidence(session, processes)
    rows: list[Json] = [
        {
            "arm": arm,
            "phase": phase,
            "eligible": eligibility(phase, transition),
            "audit": audits.get(phase, {}),
            "transition_evidence": transition,
            "error": errors.get(phase),
        }
        for phase in PHASES
    ]
    record: JsonObject = {
        "arm": arm,
        "session_id": session.session_id,
        "lifecycle": life,
        "processes": processes,
        "returned_results": returned_results(session.evidence),
        "auth_block": auth_block,
    }
    return rows, record


def run_study(
    root: Path, command: str, *, model: str = "sonnet", timeout: float = 180
) -> JsonObject:
    """Keep every completed and blocked trial in a unique preserved run directory."""
    executable = shutil.which("claude")
    if executable is None:
        raise InputError("claude", "Claude Code executable is unavailable")
    cli = inspect_cli(executable)
    if cli.get("auth_method") != "claude.ai" or cli.get("logged_in") is not True:
        raise InputError("authentication", "existing Claude subscription login is required")
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=False)
    manifest(root, command, cli)
    project = Path(__file__).resolve().parents[3]
    sessions: dict[str, Session] = {}
    for arm in ARMS:
        folder = root / "arms" / arm
        folder.mkdir(parents=True)
        settings = prepare_workspace(folder / "workspace", arm, folder / "events.jsonl", project)
        sessions[arm] = Session(
            folder / "workspace",
            folder,
            settings,
            str(uuid4()),
            executable,
            model,
            timeout,
        )
    rows: list[Json] = []
    arm_records: list[Json] = []
    blocked: str | None = None
    for arm in ARMS:
        outcomes, record = run_arm(arm, sessions[arm], blocked)
        rows.extend(outcomes)
        arm_records.append(record)
        failure = record.get("auth_block")
        blocked = None if failure is None else string(failure)
    metrics: JsonObject = {
        "study": "Claude Code governance retention",
        "rows": rows,
        "arms": arm_records,
        "limitations": [
            "One public synthetic sequential trajectory per arm; no held-out evaluation.",
            "Short manual compaction; not a long-context stress benchmark.",
            "Bounded known-tool gate; not an adversarial shell sandbox.",
            "Actual subscription cash cost unavailable; no paid API introduced.",
        ],
    }
    write_json(root / "metrics.json", metrics)
    write_report(root, metrics)
    return metrics
