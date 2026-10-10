"""Replay proposed report changes against preserved, real Phase 1 evidence."""

from __future__ import annotations

import platform
import time
from pathlib import Path

from src.intent_revalidation.model import InputError, Json, RevisionId, canonical, digest
from src.intent_revalidation.policies import Policy

from .audit import audit_revision
from .cache import run_revision
from .inputs import load_source
from .model import Column, Context, ReportRequirements, Revision
from .operations import make_context
from .outcomes import Outcome
from .reference import enumerate_plans
from .reporting import write_report
from .storage import Store


def revisions(context: Context) -> tuple[Revision, ...]:
    cases = tuple(sorted({row.case_id for row in context.source.rows}))
    if not {"D4", "D5"} <= set(cases):
        raise InputError("study", "the recorded Phase 1 source must include D4 and D5")
    columns = tuple(Column)
    reverse_columns = tuple(reversed(columns))
    return (
        Revision(RevisionId("R0"), ReportRequirements(cases, "Phase 1 results", columns)),
        Revision(RevisionId("R1"), ReportRequirements(cases, "effici-lab results", columns)),
        Revision(
            RevisionId("R2"), ReportRequirements(cases, "effici-lab results", reverse_columns)
        ),
        Revision(
            RevisionId("R3"),
            ReportRequirements(("D4", "D5"), "effici-lab results", reverse_columns),
        ),
        Revision(RevisionId("R4"), ReportRequirements(cases, "Phase 1 results", columns)),
    )


def fingerprint(store: Store) -> bytes:
    return canonical(
        [
            {
                "artifact_id": item.artifact_id,
                "step": item.step.value,
                "sha256": item.sha256,
                "input_hash": item.input_hash,
                "generation_revision": item.generation_revision,
                "key": item.key,
            }
            for item in store.cache
        ]
    )


def write_manifest(root: Path, context: Context, command: str) -> None:
    snapshots = root / "code_snapshot"
    snapshots.mkdir()
    package = Path(__file__).parent
    files = (
        *sorted(package.glob("*.py")),
        package.parent / "model.py",
        package.parent / "fixtures.py",
        package.parent / "policies.py",
    )
    hashes: dict[str, Json] = {}
    for path in files:
        relative = path.relative_to(package.parent)
        destination = snapshots / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        content = path.read_bytes()
        with destination.open("xb") as stream:
            _ = stream.write(content)
        hashes[str(relative)] = digest(content)
    manifest: Json = {
        "study": "report-workflow-phase2-entry",
        "command": command,
        "source_sha256": context.source.sha256,
        "code_files": hashes,
        "code_sha256": digest(canonical(hashes)),
        "stage_code_hashes": list(context.fingerprints),
        "environment_sha256": context.env_hash,
        "environment": {
            "python": platform.python_version(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "contract_version": context.contract_version,
        "revisions": [item.requirements.to_json() for item in revisions(context)],
        "revision_ids": [item.revision_id for item in revisions(context)],
        "case_origin": "proposed variants motivated by this project's publication and reporting",
        "source_origin": "actual preserved Phase 1 measurements; not re-executed",
        "held_out": False,
        "model_policy_evaluated": False,
        "process_isolation": False,
        "repetitions": 1,
        "policy_order": [policy.value for policy in Policy],
        "cost_model": "unit count per new report stage; not a hardware or dollar optimum",
        "timings": "operation times overlap; policy wall and evaluator overhead are separate",
        "initial_cache": "one measured seed cloned into each independent policy stream",
        "history": "each policy retains its own sequentially generated artifacts",
    }
    with (root / "manifest.json").open("xb") as stream:
        _ = stream.write(canonical(manifest))


def run_study(metrics_path: Path, root: Path, command: str) -> tuple[Outcome, ...]:
    source = load_source(metrics_path)
    context = make_context(source)
    initial_revision, *changes = revisions(context)
    root.mkdir(parents=True, exist_ok=False)
    with (root / "source_metrics.json").open("xb") as stream:
        _ = stream.write(source.content)
    write_manifest(root, context, command)
    seed = Store(root / "initial", context)
    initial = run_revision(seed, Policy.B0, initial_revision)
    with (root / "initial_metrics.json").open("xb") as stream:
        _ = stream.write(
            canonical(
                {
                    "operation_counts": dict(initial.counts),
                    "operation_duration_ns": dict(initial.durations),
                    "wall_ns": initial.finished_ns - initial.started_ns,
                }
            )
        )
    outcomes: list[Outcome] = []
    seed_fingerprint = fingerprint(seed)
    for policy in Policy:
        store = seed.clone(root / policy.value)
        if fingerprint(store) != seed_fingerprint:
            raise InputError("cache", "cloned initial state differs")
        with (store.root / "initial_cache.json").open("xb") as stream:
            _ = stream.write(seed_fingerprint)
        for revision in changes:
            cache = store.cache
            result = run_revision(store, policy, revision)
            started = time.perf_counter_ns()
            audit = audit_revision(store, revision, result.artifacts)
            reference = enumerate_plans(cache, revision.requirements, context)
            outcome = Outcome(
                revision, policy, result, audit, reference, time.perf_counter_ns() - started
            )
            outcomes.append(outcome)
            store.record("outcomes.jsonl", outcome.to_json())
            store.record("audit_assessments.jsonl", audit.to_json())
    result_outcomes = tuple(outcomes)
    with (root / "metrics.json").open("xb") as stream:
        _ = stream.write(canonical([item.to_json() for item in result_outcomes]))
    write_report(root, result_outcomes, initial)
    return result_outcomes
