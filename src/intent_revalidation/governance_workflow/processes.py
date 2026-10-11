"""Actual subscription-authenticated Claude processes and persisted execution receipts."""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from src.intent_revalidation.recovery_workflow.recording import write_json

if TYPE_CHECKING:
    from pathlib import Path

    from src.intent_revalidation.model import Json, JsonObject

AUTH_OVERRIDES: Final = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_USE_FOUNDRY",
)


@dataclass(frozen=True, slots=True)
class Session:
    """A persistent Claude identity and its isolated task workspace."""

    workspace: Path
    evidence: Path
    settings: Path
    session_id: str
    executable: str
    model: str
    timeout: float

    def arguments(self, *, resume: bool) -> list[str]:
        """Use the same supported tools and session-only settings for every arm."""
        agent = (
            '{"governance-worker":{"description":"Execute an assigned report workflow",'
            '"prompt":"Execute the assigned task in the current workspace. Follow applicable '
            'project instructions. Do not delegate further.",'
            '"tools":["Read","Write","Edit","Bash"]}}'
        )
        identity = "--resume" if resume else "--session-id"
        return [
            self.executable,
            identity,
            self.session_id,
            "--model",
            self.model,
            "--setting-sources",
            "",
            "--settings",
            str(self.settings),
            "--strict-mcp-config",
            "--mcp-config",
            '{"mcpServers":{}}',
            "--tools",
            "Read,Write,Edit,Bash,Agent",
            "--allowedTools",
            "Read,Write,Edit,Bash,Agent",
            "--permission-mode",
            "dontAsk",
            "--agents",
            agent,
        ]


def environment() -> dict[str, str]:
    """Remove paid-provider overrides without reading or copying credentials."""
    return {key: value for key, value in os.environ.items() if key not in AUTH_OVERRIDES}


def headless(session: Session, phase: str, prompt: str) -> JsonObject:
    """Launch and await an actual new OS process, preserving failure output too."""
    arguments = [
        *session.arguments(resume=True),
        "--print",
        "--verbose",
        "--output-format",
        "stream-json",
        "--include-hook-events",
        prompt,
    ]
    started = time.time()
    timed_out = False
    json_command: list[Json] = list(arguments)
    with subprocess.Popen(  # noqa: S603 - fixed executable/argv; no shell
        arguments,
        cwd=session.workspace,
        env=environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as process:
        try:
            output, errors = process.communicate(timeout=session.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            output, errors = process.communicate()
        record: JsonObject = {
            "phase": phase,
            "pid": process.pid,
            "session_id": session.session_id,
            "command": json_command,
            "started_unix": started,
            "ended_unix": time.time(),
            "returncode": process.returncode,
            "timed_out": timed_out,
        }
    with (session.evidence / f"{phase}.stdout.jsonl").open("xb") as stream:
        _ = stream.write(output)
    with (session.evidence / f"{phase}.stderr.txt").open("xb") as stream:
        _ = stream.write(errors)
    write_json(session.evidence / f"{phase}.process.json", record)
    return record
