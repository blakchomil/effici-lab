#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
# How to run: PYTHONPATH=. python3 examples/governance-guard/demo.py runs/my-new-demo
"""Exercise the real guard CLI locally; these are tool controls, not AI retention trials."""

from __future__ import annotations

import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Final

from src.intent_revalidation.fixtures import mapping
from src.intent_revalidation.model import Json, JsonObject, canonical, decode_json, digest
from src.intent_revalidation.recovery_workflow.recording import write_json

FILES: Final = {
    "CLAUDE.md": "# Active project instructions\nVerify current inputs before publishing.\n",
    "input.txt": "1\n",
    "protected.txt": "Preserve original bytes.\n",
    "verify.py": (
        "from pathlib import Path\nimport sys\n"
        "value = int(Path('input.txt').read_text())\n"
        "print('positive input verified' if value > 0 else 'negative input rejected')\n"
        "sys.exit(0 if value > 0 else 1)\n"
    ),
    "publish.py": (
        "from pathlib import Path\n"
        "Path('published.txt').write_text(Path('input.txt').read_text())\n"
    ),
}


def prepare(root: Path) -> Path:
    """Create immutable run inputs and record the exact guard source snapshot."""
    project = Path(__file__).resolve().parents[2]
    root.mkdir(parents=True, exist_ok=False)
    workspace = root / "workspace"
    workspace.mkdir()
    for name, content in FILES.items():
        _ = (workspace / name).write_text(content)
    package = project / "src/intent_revalidation/governance_guard"
    code: dict[str, Json] = {}
    for source in sorted(package.glob("*.py")):
        target = root / "code_snapshot" / source.name
        target.parent.mkdir(exist_ok=True)
        _ = shutil.copyfile(source, target)
        code[source.name] = digest(source.read_bytes())
    driver = Path(__file__).resolve()
    _ = shutil.copyfile(driver, root / "code_snapshot/demo.py")
    write_json(
        root / "manifest.json",
        {
            "case": "local reusable guard CLI controls",
            "model_calls": 0,
            "reproduction_command": (
                "PYTHONPATH=. python3 examples/governance-guard/demo.py runs/my-new-demo"
            ),
            "native_claude_lifecycles_evaluated": False,
            "code_files": code,
            "code_sha256": digest(canonical(code)),
            "driver_sha256": digest(driver.read_bytes()),
            "fixture_files": {name: digest(content.encode()) for name, content in FILES.items()},
        },
    )
    return workspace


def finish(root: Path, records: list[Json], scenarios: list[Json]) -> None:
    """Persist observed CLI outcomes without treating injected events as native lifecycles."""
    write_json(root / "commands.json", records)
    write_json(
        root / "metrics.json",
        {"scenarios": scenarios, "model_calls": 0, "native_lifecycles_evaluated": False},
    )
    passed = sum(mapping(item)["passed"] is True for item in scenarios)
    lines = [
        "# 로컬 거버넌스 도구 실제 CLI 검증",
        "",
        f"결과: {passed}/{len(scenarios)}",
        "",
        "| 상황 | 결과 |",
        "| --- | --- |",
    ]
    lines.extend(f"| {mapping(item)['name']} | {mapping(item)['passed']} |" for item in scenarios)
    lines += [
        "",
        "실제 CLI·검증 명령·게시 스크립트를 실행한 도구 기능 검증이다.",
        "훅 입력은 테스트 드라이버가 제공했다. 실제 Claude 압축·재시작·위임 평가가 아니다.",
        "모델 호출은 없고, 세 방법의 AI 준수 효과 비교는 아직 미평가다.",
        "[명령과 실제 출력](commands.json) · [지표](metrics.json) · [코드 스냅샷](manifest.json)",
    ]
    with (root / "report.md").open("x") as stream:
        _ = stream.write("\n".join(lines) + "\n")
    _ = sys.stdout.write(
        f"Guard CLI scenarios: {passed}/{len(scenarios)}\nReport: {root / 'report.md'}\n"
    )
    if passed != len(scenarios):
        raise SystemExit(1)


def denied(value: JsonObject) -> bool:
    """Interpret the guard hook's structured permission decision."""
    return mapping(value.get("hookSpecificOutput", {})).get("permissionDecision") == "deny"


def run_demo(root: Path) -> None:
    """Preserve exact commands, expected outcomes and filesystem evidence in a fresh run."""
    project = Path(__file__).resolve().parents[2]
    root = root.resolve()
    workspace = prepare(root)
    records: list[Json] = []
    scenarios: list[Json] = []
    publication = shlex.join([sys.executable, "publish.py"])

    def invoke(arguments: list[str], event: JsonObject | None = None) -> JsonObject:
        command = [
            sys.executable,
            "-m",
            "src.intent_revalidation.governance_guard",
            *arguments,
            "--root",
            str(workspace),
        ]
        result = subprocess.run(  # noqa: S603 - known local CLI argv; no shell
            command,
            input=canonical(event).decode() if event is not None else None,
            cwd=project,
            text=True,
            capture_output=True,
            check=False,
        )
        argv: list[Json] = list(command)
        record: JsonObject = {
            "command": argv,
            "input": event,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        records.append(record)
        return record

    def hook(command: str) -> JsonObject:
        result = invoke(
            ["hook"],
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": command},
            },
        )
        return mapping(decode_json(str(result["stdout"])))

    def observe(name: str, details: Json, *, passed: bool) -> None:
        scenarios.append({"name": name, "passed": passed, "details": details})

    initialized = invoke(
        [
            "init",
            "--instructions",
            "CLAUDE.md",
            "--track",
            "input.txt",
            "--track",
            "verify.py",
            "--check",
            shlex.join([sys.executable, "verify.py"]),
            "--gate",
            publication,
            "--protect",
            "protected.txt",
        ]
    )
    if initialized.get("returncode") != 0:
        write_json(root / "commands.json", records)
        raise SystemExit(str(initialized["stderr"]))
    observe(
        "before_verification_denied",
        not (workspace / "published.txt").exists(),
        passed=denied(hook(publication)),
    )
    checked = invoke(["check"])
    allowed = not denied(hook(publication))
    if allowed:
        actual = subprocess.run(
            [sys.executable, "publish.py"],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
        )
        records.append(
            {
                "command": [sys.executable, "publish.py"],
                "cwd": str(workspace),
                "returncode": actual.returncode,
                "stdout": actual.stdout,
                "stderr": actual.stderr,
            }
        )
    published = workspace / "published.txt"
    observe(
        "verified_publication_allowed",
        checked,
        passed=checked["returncode"] == 0
        and allowed
        and published.exists()
        and published.read_text() == "1\n",
    )
    _ = (workspace / "input.txt").write_text("2\n")
    observe("changed_input_denied", invoke(["status"]), passed=denied(hook(publication)))
    rechecked = invoke(["check"])
    observe(
        "recheck_restores_permission",
        rechecked,
        passed=rechecked["returncode"] == 0 and not denied(hook(publication)),
    )
    _ = (workspace / "CLAUDE.md").write_text(FILES["CLAUDE.md"] + "Use policy revision two.\n")
    observe("changed_instruction_denied", invoke(["status"]), passed=denied(hook(publication)))
    _ = (workspace / "input.txt").write_text("-1\n")
    failed = invoke(["check"])
    observe(
        "failed_verification_denied",
        failed,
        passed=failed["returncode"] == 1 and denied(hook(publication)),
    )
    protected = invoke(
        ["hook"],
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": str(workspace / "protected.txt")},
        },
    )
    ordinary = invoke(
        ["hook"],
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": str(workspace / "notes.txt")},
        },
    )
    observe(
        "protected_denied_ordinary_allowed",
        {"protected": protected, "ordinary": ordinary},
        passed=denied(mapping(decode_json(str(protected["stdout"]))))
        and not denied(mapping(decode_json(str(ordinary["stdout"])))),
    )
    injection: list[Json] = []
    reinjected = True
    for name in ("SessionStart", "SubagentStart"):
        current = invoke(["hook"], {"hook_event_name": name})
        result = mapping(decode_json(str(current["stdout"])))
        context = mapping(result.get("hookSpecificOutput", {})).get("additionalContext")
        reinjected &= isinstance(context, str) and "Use policy revision two." in context
        injection.append(current)
    observe("current_instruction_reinjected", injection, passed=reinjected)
    finish(root, records, scenarios)


if __name__ == "__main__":
    run_demo(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runs/governance-guard-20261011-01"))
