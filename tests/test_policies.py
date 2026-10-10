"""Real pipeline fixtures distinguish rejected candidates from actual invalid use."""

from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from src.intent_revalidation.audit import audit_history
from src.intent_revalidation.evaluation import evaluate
from src.intent_revalidation.fixtures import load_suite
from src.intent_revalidation.model import (
    Artifact,
    Context,
    Measurement,
    Revision,
    Task,
    Validity,
    digest,
)
from src.intent_revalidation.policies import Policy, run_policy
from src.intent_revalidation.replay import prepare_initial
from src.intent_revalidation.storage import Store


@dataclass(frozen=True, slots=True)
class History:
    store: Store
    initial: Revision
    html: Revision
    february: Revision
    cache: tuple[Artifact, ...]


@pytest.fixture
def history(tmp_path: Path) -> History:
    suite = load_suite(Path("examples/dev_cases.json"))
    source = suite.source_path.read_bytes()
    context = Context(suite.dataset_id, source, digest(source), "code-v1", "env-v1")
    store = Store(tmp_path / "history", context)
    prepare_initial(store, suite.cases[0], suite.initial)
    return History(
        store, suite.initial, suite.cases[0].target, suite.cases[1].target, tuple(store.artifacts)
    )


@pytest.mark.parametrize("restore_valid", [False, True])
def test_audit_detects_stale_overwrite_after_first_valid_publication(
    history: History,
    *,
    restore_valid: bool,
) -> None:
    store = history.store
    _ = store.revise(history.html)
    selected = run_policy(store, Policy.B1, history.html, history.cache)
    first_valid_ns = store.publish(selected, history.html)
    _ = store.publish(history.cache, history.html)
    if restore_valid:
        _ = store.publish(selected, history.html)

    result = audit_history(store, history.html)

    assert not result.final_satisfied
    assert result.first_valid_ns == first_valid_ns
    assert result.publication_count == 2 + int(restore_valid)
    assert result.invalid_publications == 1
    assert (
        result.invalid_use_events
        == result.invalid_reuse_events
        == result.invalid_reuse_artifacts
        == 1
    )


@pytest.mark.parametrize("consume_invalid", [False, True])
def test_audit_counts_actual_consumption_but_not_rejected_assessment(
    history: History,
    *,
    consume_invalid: bool,
) -> None:
    store = history.store
    _ = store.revise(history.february)
    selected = run_policy(store, Policy.B0, history.february, history.cache)
    _ = store.publish(selected, history.february)
    stale = history.cache[2]
    store.assess(
        stale,
        history.february,
        "rerun",
        evaluate(stale, history.february.requirements, store.context),
        measurement=Measurement("contract_checks", 0),
    )
    if consume_invalid:
        _ = store.complete(store.start(Task.RENDER, history.february, (stale,), "policy"))

    result = audit_history(store, history.february)

    assert result.invalid_publications == 0
    assert result.invalid_use_events == result.invalid_reuse_events == int(consume_invalid)
    assert result.invalid_reuse_artifacts == int(consume_invalid)
    assert result.final_satisfied is (not consume_invalid)


@pytest.mark.parametrize("corrupt_bytes", [False, True])
def test_b1_finds_older_matching_report_when_newest_candidate_is_invalid(
    history: History,
    *,
    corrupt_bytes: bool,
) -> None:
    store = history.store
    newer_revision = (
        history.initial
        if corrupt_bytes
        else replace(
            history.initial,
            requirements=replace(history.initial.requirements, title="Another report"),
        )
    )
    newer = store.complete(store.start(Task.RENDER, newer_revision, (history.cache[2],), "initial"))
    if corrupt_bytes:
        _ = newer.path.write_bytes(b"damaged bytes")
    cache = (*history.cache, newer)

    selected = run_policy(store, Policy.B1, history.initial, cache)

    assert selected[-1].id == history.cache[-1].id
    assert store.counters.get("policy_executions", 0) == 0
    assert (
        evaluate(selected[-1], history.initial.requirements, store.context).validity
        is Validity.VALID
    )


@pytest.mark.parametrize("field", ["source", "code", "environment", "contract"])
def test_b1_reexecutes_when_execution_context_changes(history: History, field: str) -> None:
    source = history.store.context.source + b"2026-01-15,api,777\n"
    context = history.store.context
    contexts = {
        "source": replace(context, source=source, source_sha256=digest(source)),
        "code": replace(context, code_sha256="code-v2"),
        "environment": replace(context, environment_sha256="env-v2"),
        "contract": replace(context, contract_version="contract-v2"),
    }
    store = history.store.clone(history.store.root.parent / "changed-context")
    store.context = contexts[field]

    selected = run_policy(store, Policy.B1, history.initial, tuple(store.artifacts))

    assert store.counters["policy_executions"] == 4
    assert {item.id for item in selected}.isdisjoint(item.id for item in history.cache)
    assert all(
        evaluate(item, history.initial.requirements, store.context).validity is Validity.VALID
        for item in selected
    )
    assert store.counters.get("reuse_links", 0) == 0
