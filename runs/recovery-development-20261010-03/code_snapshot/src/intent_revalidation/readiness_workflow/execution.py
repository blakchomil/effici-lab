"""Execute equal-cache report arms without exposing evaluator expectations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter_ns
from typing import TYPE_CHECKING
from uuid import uuid4

from src.intent_revalidation.model import InputError, RevisionId, canonical, digest
from src.intent_revalidation.report_workflow.cache import run_revision
from src.intent_revalidation.report_workflow.model import Revision

from .composition import compose
from .interpretation import interpret
from .model import Control, Interpretation, Meaning

if TYPE_CHECKING:
    from src.intent_revalidation.policies import Policy
    from src.intent_revalidation.report_workflow.cache import Result
    from src.intent_revalidation.report_workflow.model import ReportRequirements
    from src.intent_revalidation.report_workflow.storage import Store

    from .model import Clarification, Snapshot


@dataclass(frozen=True, slots=True)
class CaseInputs:
    """Shared observed inputs and the unchanged numeric report requirements."""

    snapshot: Snapshot
    clarification: Clarification
    requirements: ReportRequirements
    original_request: bytes
    previous_report: bytes


@dataclass(frozen=True, slots=True)
class Arm:
    """A policy paired with one interpretation strategy or the confirmed reference."""

    control: Control | None
    policy: Policy

    @property
    def name(self) -> str:
        return f"{self.control.value if self.control else 'confirmed'}-{self.policy.value}"


@dataclass(frozen=True, slots=True)
class ArmRun:
    """Actual work with nonoverlapping outer durations and nested stage diagnostics."""

    arm: Arm
    store: Store
    revision: Revision
    interpretation: Interpretation
    numeric: Result
    document: Path
    interpretation_ns: int
    composition_ns: int
    wall_ns: int


def execute_arm(store: Store, arm: Arm, inputs: CaseInputs) -> ArmRun:
    """Consume actual bytes and publish one immutable readiness document."""
    started = perf_counter_ns()
    interpretation = (
        interpret(inputs.clarification, arm.control)
        if arm.control is not None
        else Interpretation(Meaning.READINESS, 0, ())
    )
    interpretation_ns = perf_counter_ns() - started
    if interpretation.meaning != Meaning.READINESS:
        raise InputError("interpretation", "readiness meaning remains unresolved or unsupported")
    revision = Revision(RevisionId("readiness-R1"), inputs.requirements)
    numeric = run_revision(store, arm.policy, revision)
    composition_started = perf_counter_ns()
    report = numeric.artifacts[-1]
    content = report.path.read_bytes()
    cached = report.generation_revision != revision.revision_id
    attempt_id = f"compose-{uuid4().hex}"
    store.record(
        "composition-attempts.jsonl",
        {
            "action": "start",
            "attempt_id": attempt_id,
            "revision": revision.revision_id,
            "started_ns": composition_started,
        },
    )
    store.record(
        "readiness-events.jsonl",
        {
            "action": "consume",
            "role": "numeric_report",
            "artifact_id": report.artifact_id,
            "actual_sha256": digest(content),
            "expected_sha256": report.sha256,
            "cached": cached,
        },
    )
    store.record(
        "readiness-events.jsonl",
        {
            "action": "consume",
            "role": "repository_facts",
            "actual_sha256": digest(inputs.snapshot.content),
            "expected_sha256": inputs.snapshot.sha256,
            "cached": False,
        },
    )
    produced = compose(content, inputs.snapshot, store.context.source.sha256)
    destination = store.root / "readiness-report.md"
    with destination.open("xb") as stream:
        _ = stream.write(produced)
    finished = perf_counter_ns()
    store.record(
        "composition-attempts.jsonl",
        {
            "action": "complete",
            "attempt_id": attempt_id,
            "revision": revision.revision_id,
            "completed_ns": finished,
            "output_sha256": digest(produced),
            "input_report_sha256": digest(content),
            "facts_sha256": inputs.snapshot.sha256,
            "code_sha256": digest(Path(__file__).with_name("composition.py").read_bytes()),
            "environment_sha256": store.context.env_hash,
        },
    )
    store.record(
        "readiness-events.jsonl",
        {
            "action": "publish",
            "role": "readiness_report",
            "actual_sha256": digest(produced),
            "expected_sha256": digest(produced),
            "cached": False,
        },
    )
    with (store.root / "current-readiness.json").open("xb") as stream:
        _ = stream.write(canonical({"path": destination.name, "sha256": digest(produced)}))
    return ArmRun(
        arm,
        store,
        revision,
        interpretation,
        numeric,
        destination,
        interpretation_ns,
        finished - composition_started,
        perf_counter_ns() - started,
    )
