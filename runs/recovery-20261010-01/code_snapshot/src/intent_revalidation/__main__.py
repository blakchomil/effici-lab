"""Run: python3 -m src.intent_revalidation; only the Python standard library is required."""

import argparse
import shlex
import sys
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .experiment import run_experiment
from .model import InputError
from .reporting import write_report


class Arguments(argparse.Namespace):
    """Typed CLI boundary; argparse mutates only these declared supported fields."""

    def __init__(self) -> None:
        super().__init__()
        self.cases: Path = Path("examples/dev_cases.json")
        self.output: Path = Path("runs")
        self.run_id: str | None = None


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1 public development comparison: B0/B1/B2")
    _ = parser.add_argument("--cases", type=Path, default=Path("examples/dev_cases.json"))
    _ = parser.add_argument("--output", type=Path, default=Path("runs"))
    _ = parser.add_argument(
        "--run-id",
        default=None,
        help="unique output folder name; existing runs are never overwritten",
    )
    args = Arguments()
    _ = parser.parse_args(namespace=args)
    cases_path = args.cases.resolve()
    output = args.output.resolve()
    run_id = (
        args.run_id
        if args.run_id is not None
        else (
            datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d-%H%M%S")
            + "-"
            + uuid.uuid4().hex[:8]
        )
    )
    if not run_id or any(
        char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        for char in run_id
    ):
        parser.error("run-id must contain only ASCII letters, numbers, '-' or '_'")
    root = output / run_id
    try:
        outcomes = run_experiment(
            cases_path,
            root,
            shlex.join(["python3", "-m", "src.intent_revalidation", *sys.argv[1:]]),
        )
        write_report(root, outcomes)
    except (InputError, OSError, ValueError) as error:
        print(f"Phase 1 failed: {error}", file=sys.stderr)
        return 2
    passed = sum(result.audit.final_satisfied for result in outcomes)
    print(f"Final contracts satisfied: {passed}/{len(outcomes)}")
    print(f"Report: {root / 'report.md'}")
    return 0 if passed == len(outcomes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
