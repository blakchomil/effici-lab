"""Run the bounded recovery comparison without network or model calls."""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

from src.intent_revalidation.model import InputError
from src.intent_revalidation.report_workflow.__main__ import identifier

from .study import run_study


class Arguments(argparse.Namespace):
    """Typed paths and explicit optional run identity at the CLI boundary."""

    metrics: Path = Path("runs/phase1-20261010-01/metrics.json")
    output: Path = Path("runs")
    run_id: str | None = None


def main() -> int:
    parser = argparse.ArgumentParser(description="Public synthetic between-revision recovery study")
    _ = parser.add_argument("--metrics", type=Path, default=Arguments.metrics)
    _ = parser.add_argument("--output", type=Path, default=Arguments.output)
    _ = parser.add_argument("--run-id", help="unique folder name; existing runs are preserved")
    arguments = Arguments()
    _ = parser.parse_args(namespace=arguments)
    command = "python -m src.intent_revalidation.recovery_workflow "
    command += " ".join(shlex.quote(item) for item in sys.argv[1:])
    try:
        selected = identifier(arguments.run_id)
        if arguments.run_id is None:
            selected = selected.replace("report-", "recovery-", 1)
        destination = arguments.output / selected
        outcomes = run_study(arguments.metrics, destination, command.strip())
    except (InputError, OSError, ValueError, UnicodeError) as error:
        _ = sys.stderr.write(f"Recovery comparison failed: {error}\n")
        return 2
    satisfied = sum(item.audit.final_satisfied for item in outcomes)
    _ = sys.stdout.write(f"Recovery workflow contracts satisfied: {satisfied}/{len(outcomes)}\n")
    _ = sys.stdout.write(f"Report: {destination.resolve() / 'report.md'}\n")
    return 0 if satisfied == len(outcomes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
