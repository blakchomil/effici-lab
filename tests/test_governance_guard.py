from __future__ import annotations

import shlex
import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

from src.intent_revalidation.fixtures import mapping, sequence, string
from src.intent_revalidation.governance_guard.__main__ import Arguments, initialize
from src.intent_revalidation.governance_guard.hooks import decision
from src.intent_revalidation.governance_guard.policy import confined, load
from src.intent_revalidation.governance_guard.receipts import check, status
from src.intent_revalidation.model import InputError, canonical, decode_json

if TYPE_CHECKING:
    from pathlib import Path

    from src.intent_revalidation.model import JsonObject


@pytest.fixture
def project(tmp_path: Path) -> Path:
    _ = (tmp_path / "CLAUDE.md").write_text("Keep evidence before publishing.\n")
    _ = (tmp_path / "input.txt").write_text("valid\n")
    _ = (tmp_path / "verify.py").write_text(
        """from pathlib import Path
import sys
sys.exit(0 if Path('input.txt').read_text() == 'valid\\n' else 1)
"""
    )
    args = Arguments()
    args.root = tmp_path
    args.check = shlex.join([sys.executable, "verify.py"])
    args.track = ["input.txt", "verify.py"]
    args.gate = ["python3 publish.py"]
    args.protect = ["protected.txt"]
    _ = initialize(args)
    return tmp_path


def bash(command: str = "python3 publish.py") -> JsonObject:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }


def denied(output: JsonObject) -> bool:
    return mapping(output.get("hookSpecificOutput", {})).get("permissionDecision") == "deny"


def test_gate_denies_when_check_missing(project: Path) -> None:
    assert denied(decision(load(project), bash()))


def test_gate_allows_when_current_check_passed(project: Path) -> None:
    _ = check(load(project))
    assert decision(load(project), bash()) == {}


@pytest.mark.parametrize("filename", ["input.txt", "CLAUDE.md", ".governance/policy.json"])
def test_gate_denies_when_fingerprint_changes(project: Path, filename: str) -> None:
    _ = check(load(project))
    path = project / filename
    if filename.endswith("json"):
        policy = mapping(decode_json(path.read_text()))
        policy["version"] = 2
        _ = path.write_bytes(canonical(policy))
    else:
        _ = path.write_text("changed\n")
    assert denied(decision(load(project), bash()))


def test_check_records_failure_when_verifier_rejects(project: Path) -> None:
    _ = (project / "input.txt").write_text("invalid\n")
    receipt = check(load(project))
    assert receipt["exit_code"] == 1
    assert status(load(project))["valid"] is False


def test_check_rejects_when_verifier_changes_tracked_source(project: Path) -> None:
    _ = (project / "verify.py").write_text(
        "from pathlib import Path\nPath('input.txt').write_text('changed')\n"
    )
    receipt = check(load(project))
    assert receipt["exit_code"] == 0
    assert receipt["passed"] is False


def test_latest_failure_supersedes_success_when_sources_are_unchanged(project: Path) -> None:
    _ = (project / "verify.py").write_text(
        "from pathlib import Path\nimport sys\nsys.exit(int(Path('fail').exists()))\n"
    )
    assert check(load(project))["passed"] is True
    _ = (project / "fail").write_text("untracked external condition")
    _ = check(load(project))
    assert status(load(project))["valid"] is False


def test_check_records_failure_when_timeout_expires(project: Path) -> None:
    _ = (project / "verify.py").write_text("while True: pass\n")
    receipt = check(load(project), timeout=0.02)
    assert receipt["passed"] is False
    assert "timed out" in string(receipt["stderr"])


def test_status_invalidates_when_tracked_file_is_added(project: Path) -> None:
    path = project / ".governance/policy.json"
    raw = mapping(decode_json(path.read_text()))
    raw["tracked"] = ["*.txt", "verify.py"]
    _ = path.write_bytes(canonical(raw))
    _ = check(load(project))
    _ = (project / "new.txt").write_text("additional input")
    assert status(load(project))["valid"] is False


@pytest.mark.parametrize("event", ["SessionStart", "SubagentStart"])
def test_hook_injects_current_instructions_when_session_starts(project: Path, event: str) -> None:
    output = decision(load(project), {"hook_event_name": event})
    assert "Keep evidence before publishing." in string(
        mapping(output["hookSpecificOutput"])["additionalContext"]
    )


@pytest.mark.parametrize(
    "command",
    [
        "true; python3 publish.py",
        "python3 publish.py | cat",
        "echo $(python3 publish.py)",
        "FOO=bar python3 publish.py",
        "env FOO=bar python3 publish.py",
    ],
)
def test_gate_denies_when_known_command_is_compound(project: Path, command: str) -> None:
    _ = check(load(project))
    assert denied(decision(load(project), bash(command)))


@pytest.mark.parametrize("filename", ["protected.txt", ".governance/policy.json"])
def test_gate_denies_when_editing_protected_file(project: Path, filename: str) -> None:
    assert denied(
        decision(
            load(project),
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Edit",
                "tool_input": {"file_path": filename},
            },
        )
    )


def test_init_preserves_existing_policy_when_run_twice(project: Path) -> None:
    original = (project / ".governance/policy.json").read_bytes()
    args = Arguments()
    args.root = project
    args.check = "false"
    with pytest.raises(FileExistsError):
        _ = initialize(args)
    assert (project / ".governance/policy.json").read_bytes() == original


def test_path_rejects_when_symlink_escapes(
    project: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    outside = tmp_path_factory.mktemp("outside")
    (project / "escape").symlink_to(outside, target_is_directory=True)
    with pytest.raises(InputError):
        _ = confined(project, "escape/data.txt")


def test_settings_hook_runs_when_cwd_is_target_project(project: Path) -> None:
    settings = mapping(decode_json((project / ".governance/session-settings.json").read_text()))
    entry = mapping(sequence(mapping(settings["hooks"])["SessionStart"])[0])
    command = string(mapping(sequence(entry["hooks"])[0])["command"])
    result = subprocess.run(  # noqa: S603 -- execute generated hook integration command
        ["/bin/sh", "-c", command],
        cwd=project,
        text=True,
        capture_output=True,
        input=canonical({"hook_event_name": "SessionStart"}).decode(),
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Keep evidence before publishing." in result.stdout
