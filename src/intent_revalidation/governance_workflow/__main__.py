"""Run real subscription-backed governance trials only on explicit CLI invocation."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

from src.intent_revalidation.fixtures import mapping, sequence
from src.intent_revalidation.model import InputError, JsonObject
from src.intent_revalidation.report_workflow.__main__ import identifier

from .study import ARMS, PHASES, run_study


class Arguments(argparse.Namespace):
    """Typed CLI boundary, following the existing standard-library experiment commands."""

    output: Path = Path("runs")
    run_id: str | None = None
    model: str = "sonnet"
    timeout: float = 180


def main() -> int:
    parser = argparse.ArgumentParser(description="Actual Claude Code governance comparison")
    _ = parser.add_argument("--output", type=Path, default=Arguments.output)
    _ = parser.add_argument("--run-id", help="unique run directory, never overwritten")
    _ = parser.add_argument("--model", default=Arguments.model)
    _ = parser.add_argument("--timeout", type=float, default=Arguments.timeout)
    arguments = Arguments()
    _ = parser.parse_args(namespace=arguments)
    command = "python -m src.intent_revalidation.governance_workflow "
    command += shlex.join(sys.argv[1:])
    if arguments.timeout <= 0:
        _ = sys.stderr.write("Governance experiment failed: timeout must be positive\n")
        return 2
    try:
        chosen = identifier(arguments.run_id)
        if arguments.run_id is None:
            chosen = chosen.replace("report-", "governance-", 1)
        root = arguments.output / chosen
        metrics = run_study(root, command.strip(), model=arguments.model, timeout=arguments.timeout)
    except (InputError, OSError, ValueError, subprocess.SubprocessError) as error:
        _ = sys.stderr.write(f"Governance experiment failed: {error}\n")
        return 2
    _ = sys.stdout.write(f"Report: {root.resolve() / 'report.md'}\n")
    return 0 if all_rows_observed(metrics) else 1


def all_rows_observed(metrics: JsonObject) -> bool:
    """Require all twelve actual tasks, including controls, to be observed and satisfied."""
    rows = sequence(metrics.get("rows", []))
    return len(rows) == len(ARMS) * len(PHASES) and all(
        mapping(row).get("eligible") is True
        and mapping(mapping(row).get("audit", {})).get("satisfied") is True
        and mapping(row).get("error") is None
        for row in rows
    )


if __name__ == "__main__":
    raise SystemExit(main())
