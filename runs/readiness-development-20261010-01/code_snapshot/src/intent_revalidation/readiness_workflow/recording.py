"""Preserve run inputs, executable code and the complete comparison report."""

from __future__ import annotations

import platform
import shlex
import sys
from pathlib import Path

from src.intent_revalidation.fixtures import field, mapping, string
from src.intent_revalidation.model import Json, canonical, digest
from src.intent_revalidation.report_workflow.inputs import count


def write_json(path: Path, value: Json) -> None:
    """Create new evidence exclusively; never replace a previous run's record."""
    with path.open("xb") as stream:
        _ = stream.write(canonical(value))


def preserve_inputs(root: Path, case: Path, metrics: Path) -> None:
    """Capture executable source and all frozen observations before the seed runs."""
    repository = Path(__file__).resolve().parents[3]
    snapshots = root / "code_snapshot"
    source_hashes: dict[str, Json] = {}
    for path in sorted((repository / "src").rglob("*.py")):
        destination = snapshots / path.relative_to(repository)
        destination.parent.mkdir(parents=True, exist_ok=True)
        content = path.read_bytes()
        with destination.open("xb") as stream:
            _ = stream.write(content)
        source_hashes[str(path.relative_to(repository))] = digest(content)
    inputs = root / "inputs"
    inputs.mkdir()
    files = (
        case / "request.md",
        case / "clarification-20261010.json",
        case / "current-facts-20261010.json",
        case / "evidence-20261010.json",
        case / "protocol-20261010.md",
        case / "runs/observed-02/retitled-report.md",
        metrics,
    )
    input_hashes: dict[str, Json] = {}
    for path in files:
        content = path.read_bytes()
        with (inputs / path.name).open("xb") as stream:
            _ = stream.write(content)
        input_hashes[str(path.relative_to(repository))] = digest(content)
    write_json(
        root / "manifest.json",
        {
            "study": "human-clarified-readiness-development-case",
            "repetitions": 5,
            "command": shlex.join(
                [sys.executable, "-m", "src.intent_revalidation.readiness_workflow", *sys.argv[1:]]
            ),
            "code_files": source_hashes,
            "code_sha256": digest(canonical(source_hashes)),
            "input_files": input_hashes,
            "input_sha256": digest(canonical(input_hashes)),
            "environment": {
                "python": platform.python_version(),
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
            },
            "human_confirmed": True,
            "external_feedback": False,
            "held_out": False,
            "process_isolation": False,
            "evaluated_model_policy": False,
            "runtime_github_calls": 0,
            "fact_capture": "read-only commands and timings in inputs/evidence-20261010.json",
            "real_human_questions": 1,
            "human_wait_ns": None,
            "human_repair_ns": None,
            "implementation_model_usage_and_cost": "unmeasured, excluded from runtime",
            "order": "five cyclic rotations of five arms; each arm at each position once",
            "numeric_contract": "unchanged numeric report; prior observed-02 bytes retained",
            "minimum_scope": "exhaustive three-step numeric bound plus one composition",
        },
    )


def write_report(root: Path, outcomes: tuple[Json, ...]) -> None:
    """Show all measured runs without inferring a time or dollar advantage."""
    rows = [mapping(value) for value in outcomes]
    lines = [
        "# Human-clarified readiness report comparison",
        "",
        "One maintainer request, one real confirmation, five repetitions of the same public case.",
        "Both interpretation controls use the same exact-choice parser and recorded response.",
        "Natural-language generalization and the benefit of asking a question are unmeasured.",
        "",
        "| repeat | arm | valid | stages | minimum | reused | invalid reuse | runtime ms |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    lines.extend(
        "| "
        + " | ".join(
            [
                str(field(row, "repetition")),
                string(field(row, "arm")),
                str(field(row, "final_satisfied")),
                str(field(row, "total_stage_executions")),
                str(field(row, "minimum_total_stage_executions")),
                str(field(row, "numeric_stage_reuses")),
                str(field(row, "invalid_reuse_events")),
                f"{count(field(row, 'runtime_wall_ns')) / 1_000_000:.3f}",
            ]
        )
        + " |"
        for row in rows
    )
    passed = sum(field(row, "final_satisfied") is True for row in rows)
    valid_controls = all(
        field(row, "final_satisfied") is True and field(row, "excess_stage_executions") == 0
        for row in rows
        if field(row, "arm") != "confirmed-B0"
    )
    lines += [
        "",
        f"Final contracts satisfied: {passed}/{len(rows)}.",
        "",
        "Simple clarified controls suffice; this case does not justify an AI comparison."
        if valid_controls
        else "A control failed or exceeded the stage-count minimum; inspect metrics.json.",
        "",
        "Preserved numbers and source are checked independently from original metrics bytes.",
        "All intermediate numeric uses and readiness consumption/publication records are audited.",
        "B2 recomputations are counted and timed as checks. Stage reuse still incurs that work.",
        "Nested times overlap. Runtime, clone, preparation/seed and evaluator costs are separate.",
        "The real response is replayed; no new human interaction occurs per repetition.",
        "Human repair time, implementation-model costs and local dollar costs are unmeasured.",
        "Stable savings, external utility, broad safety and AI advantage remain unestablished.",
        "Evaluated model calls/tokens/paid model API cost and original experiment reruns: zero.",
        "",
    ]
    with (root / "report.md").open("xb") as stream:
        _ = stream.write("\n".join(lines).encode())
