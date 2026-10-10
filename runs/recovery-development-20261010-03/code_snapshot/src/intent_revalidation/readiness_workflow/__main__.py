"""Execute the human-clarified readiness development case through its CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.intent_revalidation.fixtures import field, mapping
from src.intent_revalidation.model import InputError
from src.intent_revalidation.report_workflow.__main__ import identifier

from .study import run_study


class Arguments(argparse.Namespace):
    """Typed paths from the argparse input boundary."""

    metrics: Path = Path("runs/phase1-20261010-01/metrics.json")
    case: Path = Path("examples/support-readiness")
    output: Path = Path("runs")
    run_id: str | None = None


def main() -> int:
    """Reject unresolved meaning and protected run IDs before a comparison proceeds."""
    parser = argparse.ArgumentParser(description="Human-clarified readiness development comparison")
    _ = parser.add_argument("--metrics", type=Path, default=Arguments.metrics)
    _ = parser.add_argument("--case", type=Path, default=Arguments.case)
    _ = parser.add_argument("--output", type=Path, default=Arguments.output)
    _ = parser.add_argument("--run-id", help="new run folder; existing evidence is preserved")
    arguments = Arguments()
    _ = parser.parse_args(namespace=arguments)
    try:
        root = arguments.output / identifier(arguments.run_id)
        outcomes = run_study(arguments.metrics, arguments.case, root)
    except (InputError, OSError, ValueError, UnicodeError) as error:
        _ = sys.stderr.write(f"Readiness comparison failed: {error}\n")
        return 2
    satisfied = sum(field(mapping(row), "final_satisfied") is True for row in outcomes)
    _ = sys.stdout.write(f"Readiness contracts satisfied: {satisfied}/{len(outcomes)}\n")
    _ = sys.stdout.write(f"Report: {root.resolve() / 'report.md'}\n")
    return 0 if satisfied == len(outcomes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
