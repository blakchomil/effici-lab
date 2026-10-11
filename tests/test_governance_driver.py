from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

from src.intent_revalidation.governance_workflow import __main__ as cli
from src.intent_revalidation.governance_workflow import study
from src.intent_revalidation.governance_workflow.processes import Session
from src.intent_revalidation.governance_workflow.recording import (
    returned_results,
    transcript_evidence,
)
from src.intent_revalidation.governance_workflow.stream import stream_error
from src.intent_revalidation.governance_workflow.study import (
    eligibility,
    run_arm,
    transition_evidence,
)
from src.intent_revalidation.model import InputError, Json, JsonObject, canonical

if TYPE_CHECKING:
    from collections.abc import Callable

REPO: Final = Path(__file__).parents[1]


def _metrics() -> JsonObject:
    rows: list[Json] = [
        {"arm": arm, "phase": phase, "eligible": True, "audit": {"satisfied": True}, "error": None}
        for arm in ("G0", "G1", "G2")
        for phase in ("initial", "compact", "restart", "delegation")
    ]
    return {"rows": rows}


@pytest.mark.parametrize("complete", [True, False])
def test_stream_errors_require_a_completed_result_line(tmp_path: Path, *, complete: bool) -> None:
    # Given a structured runtime error that may still be arriving over a pipe.
    path = tmp_path / "stdout.jsonl"
    content = canonical({"type": "result", "is_error": True, "result": "OAuth token expired"})
    _ = path.write_bytes(content if complete else content.rstrip(b"\n"))
    # When the streaming error reader examines the saved bytes.
    observed = stream_error(str(path))
    # Then only a complete result establishes failure.
    assert observed == ("OAuth token expired" if complete else None)


def test_assistant_discussing_auth_is_not_a_runtime_error(tmp_path: Path) -> None:
    # Given normal assistant output mentioning an error and a successful result.
    path = tmp_path / "stdout.jsonl"
    _ = path.write_bytes(
        canonical({"type": "assistant", "message": "OAuth token expired is an example error"})
        + canonical({"type": "result", "is_error": False, "result": "Completed"})
    )
    # When the structured error reader inspects those events.
    observed = stream_error(str(path))
    # Then narrative text cannot be classified as a runtime error.
    assert observed is None


def test_stream_reader_rejects_unnamed_descriptor() -> None:
    # Given an unnamed file descriptor rather than an evidence filename.
    descriptor = 1
    # When it crosses the stream-reader boundary.
    with pytest.raises(InputError, match="named file"):
        _ = stream_error(descriptor)
    # Then the invalid boundary is explicit rather than reading unrelated bytes.


@pytest.mark.parametrize(
    ("phase", "required"),
    [
        ("initial", ("startup",)),
        ("compact", ("manual_precompact", "compact_sessionstart")),
        ("restart", ("new_pid", "same_resumed_uuid")),
        ("delegation", ("parent_agent_tool_call", "matching_child_lifecycle", "child_transcript")),
    ],
)
def test_every_lifecycle_prerequisite_is_required(phase: str, required: tuple[str, ...]) -> None:
    # Given all required receipts for this claimed transition.
    complete: JsonObject = dict.fromkeys(required, True)
    incomplete = [
        {key: value for key, value in complete.items() if key != missing} for missing in required
    ]
    # When complete and individually incomplete evidence sets are classified.
    observed = [eligibility(phase, value) for value in (complete, *incomplete)]
    # Then every named prerequisite contributes to eligibility.
    assert observed == [True, *[False for _ in required]]


def test_unknown_transition_is_rejected() -> None:
    # Given a phase outside the public protocol.
    phase = "imaginary_transition"
    # When a caller attempts to score it.
    with pytest.raises(InputError, match="phase"):
        _ = eligibility(phase, {})
    # Then no default success is assigned.


@pytest.mark.parametrize("fault", ["none", "missing", "ineligible", "failed_audit", "error"])
def test_cli_success_requires_all_planned_rows(fault: str) -> None:
    # Given the complete twelve-row comparison with at most one defect.
    metrics = _metrics()
    rows = metrics["rows"]
    assert isinstance(rows, list)
    if fault == "missing":
        _ = rows.pop()
    row = rows[0]
    assert isinstance(row, dict)
    if fault == "ineligible":
        row["eligible"] = False
    if fault == "failed_audit":
        row["audit"] = {"satisfied": False}
    if fault == "error":
        row["error"] = "runtime failed"
    # When CLI completion is evaluated independently of report prose.
    observed = cli.all_rows_observed(metrics)
    # Then missing, ineligible and failed observations cannot produce success.
    assert observed is (fault == "none")


@pytest.mark.parametrize("successful", [True, False])
def test_cli_exit_reflects_audit_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    *,
    successful: bool,
) -> None:
    # Given fixed study output at the external execution boundary; no model is called.
    metrics: JsonObject = _metrics() if successful else {"rows": []}

    def study_stub(root: Path, command: str, *, model: str, timeout: float) -> JsonObject:
        assert root == tmp_path / "case"
        assert command.startswith("python -m src.intent_revalidation.governance_workflow")
        assert model == "sonnet"
        assert timeout > 0
        return metrics

    monkeypatch.setattr(cli, "run_study", study_stub)
    monkeypatch.setattr(sys, "argv", ["governance", "--output", str(tmp_path), "--run-id", "case"])
    # When the public CLI entrypoint runs against those observed results.
    code = cli.main()
    # Then its exit status distinguishes a complete study from an empty one.
    assert code == (0 if successful else 1)
    assert "Report:" in capsys.readouterr().out


def test_cli_preserves_subprocess_timeout_as_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given a timeout at the external execution boundary.
    def timeout_stub(root: Path, command: str, *, model: str, timeout: float) -> JsonObject:
        assert root == tmp_path / "case"
        assert command
        assert model
        raise subprocess.TimeoutExpired("local-test-no-model", timeout)

    monkeypatch.setattr(cli, "run_study", timeout_stub)
    monkeypatch.setattr(sys, "argv", ["governance", "--output", str(tmp_path), "--run-id", "case"])
    # When the CLI handles that actual exception class.
    code = cli.main()
    # Then it returns an execution failure and preserves the reason.
    assert code == 2
    assert "timed out" in capsys.readouterr().err


@pytest.mark.parametrize("argument", ["--help", "--timeout=0", "--timeout=-1", "--timeout=invalid"])
def test_real_cli_parses_help_and_invalid_timeouts(argument: str) -> None:
    # Given CLI arguments that must finish before model or authentication access.
    command = [sys.executable, "-m", "src.intent_revalidation.governance_workflow", argument]
    # When the actual module executable receives them.
    result = subprocess.run(command, cwd=REPO, capture_output=True, text=True, check=False)  # noqa: S603
    # Then help succeeds and invalid timeouts fail at the local argument boundary.
    assert result.returncode == (0 if argument == "--help" else 2)
    assert "timeout" in result.stdout + result.stderr


def _session(root: Path) -> Session:
    return Session(
        root / "workspace", root, root / "settings.json", "session-a", "unused", "test", 1
    )


@pytest.mark.parametrize("trigger", ["manual", "auto", None])
def test_transition_requires_manual_compact_receipt(tmp_path: Path, trigger: str | None) -> None:
    # Given lifecycle records from a constructed manual or automatic compaction.
    events: list[Json] = [
        {"hook_event_name": "PreCompact", "trigger": trigger},
        {"hook_event_name": "SessionStart", "source": "compact", "session_id": "session-a"},
    ]
    _ = (tmp_path / "events.jsonl").write_bytes(b"".join(canonical({"payload": p}) for p in events))
    # When the real transition evidence collector parses those records.
    observed, _ = transition_evidence(_session(tmp_path), [])
    # Then automatic or unidentified compaction cannot satisfy the manual protocol.
    assert eligibility("compact", observed) is (trigger == "manual")


def test_sidechain_agent_call_is_not_parent_delegation(tmp_path: Path) -> None:
    # Given a lifecycle-named child transcript containing its own Agent call.
    child = tmp_path / "child.jsonl"
    _ = child.write_bytes(
        canonical(
            {
                "isSidechain": True,
                "message": {
                    "content": [{"type": "tool_use", "name": "Agent"}],
                },
            }
        )
    )
    events = tmp_path / "events.jsonl"
    _ = events.write_bytes(canonical({"payload": {"agent_transcript_path": str(child)}}))
    # When transcript evidence is collected from the real files.
    observed = transcript_evidence(tmp_path, events)
    # Then child activity supplies no evidence of a parent delegation call.
    assert observed["child_transcript"] is True
    assert observed["parent_agent_tool_call"] is False


def test_returned_results_preserve_complete_usage_and_ignore_partial_tail(tmp_path: Path) -> None:
    # Given an actual result record followed by an unfinished stream fragment.
    result: JsonObject = {"type": "result", "usage": {"input_tokens": 17}}
    _ = (tmp_path / "run.stdout.jsonl").write_bytes(canonical(result) + b'{"type":')
    # When returned evidence is collected.
    observed = returned_results(tmp_path)
    # Then complete usage survives without inventing a result for the partial tail.
    assert observed == [result]


def test_later_process_error_does_not_taint_prior_phase(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given constructed execution boundaries completing initial/compact before restart fails.
    def continuous_stub(
        session: Session, events: Path, capture: Callable[[str], None]
    ) -> JsonObject:
        assert session.session_id == "session-a"
        _ = events.write_bytes(
            canonical(
                {
                    "payload": {
                        "hook_event_name": "SessionStart",
                        "source": "startup",
                        "session_id": "session-a",
                    }
                }
            )
        )
        capture("initial")
        capture("compact")
        return {"pid": 101, "returncode": 0, "error": None}

    def restart_stub(session: Session, phase: str, prompt: str) -> JsonObject:
        assert session.session_id == "session-a"
        assert phase == "restart"
        assert prompt
        return {"pid": 102, "returncode": 1, "timed_out": False}

    monkeypatch.setattr(study, "continuous", continuous_stub)
    monkeypatch.setattr(study, "headless", restart_stub)
    # When per-arm recording preserves the results of those boundaries.
    rows, _ = run_arm("G0", _session(tmp_path), None)
    # Then the restart error is isolated from previously completed phases.
    assert isinstance(rows[0], dict)
    assert isinstance(rows[1], dict)
    assert isinstance(rows[2], dict)
    assert rows[0]["error"] is None
    assert rows[1]["error"] is None
    assert rows[2]["error"] is not None
