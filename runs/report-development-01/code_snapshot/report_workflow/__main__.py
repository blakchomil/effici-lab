"""Execute the report follow-up without rerunning the source experiment."""

from __future__ import annotations

import argparse
import secrets
import shlex
import sys
from datetime import datetime
from pathlib import Path
from typing import assert_never
from zoneinfo import ZoneInfo

from ..model import InputError
from .study import run_study


class Arguments(argparse.Namespace):
    """The parsed CLI boundary provides typed paths and an optional run identity."""

    metrics: Path
    output: Path
    run_id: str | None


def identifier(value: str | None) -> str:
    match value:
        case None:
            stamp = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d-%H%M%S")
            return f"report-{stamp}-{secrets.token_hex(4)}"
        case str() as selected:
            if not selected or any(
                char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
                for char in selected
            ):
                raise InputError("run-id", "expected alphanumeric characters, dash or underscore")
            return selected
        case unreachable:
            assert_never(unreachable)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report follow-up study: actual Phase 1 evidence, proposed change cases"
    )
    _ = parser.add_argument(
        "--metrics", type=Path, default=Path("runs/phase1-20261010-01/metrics.json")
    )
    _ = parser.add_argument("--output", type=Path, default=Path("runs"))
    _ = parser.add_argument("--run-id", help="unique folder name; existing runs are preserved")
    arguments = Arguments()
    _ = parser.parse_args(namespace=arguments)
    command = "python3 -m src.intent_revalidation.report_workflow"
    command += " " + " ".join(shlex.quote(item) for item in sys.argv[1:])
    try:
        destination = arguments.output / identifier(arguments.run_id)
        outcomes = run_study(arguments.metrics, destination, command.strip())
    except (InputError, OSError, ValueError, UnicodeError) as error:
        print(f"Report follow-up failed: {error}", file=sys.stderr)
        return 2
    satisfied = sum(item.audit.final_satisfied for item in outcomes)
    print(f"Report workflow contracts satisfied: {satisfied}/{len(outcomes)}")
    print(f"Report: {destination.resolve() / 'report.md'}")
    return 0 if satisfied == len(outcomes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
