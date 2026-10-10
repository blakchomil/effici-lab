"""Ordered local event replay with real computation and no claim of parallel cancellation."""

from .fixtures import Case
from .model import Artifact, InputError, Revision
from .storage import Attempt, Store


def prepare_initial(store: Store, case: Case, initial: Revision) -> None:
    store.append("revisions.jsonl", initial.to_json())
    selected: list[Artifact] = []
    for task in case.completed_tasks:
        selected.append(store.complete(store.start(task, initial, tuple(selected[-1:]), "initial")))
    if len(selected) == 4:
        _ = store.publish(tuple(selected), initial)


def replay(store: Store, case: Case, initial: Revision) -> int:
    """Activate policy only after the same late attempt actually completes under r0."""
    if not case.events:
        return store.revise(case.target)
    late: Attempt | None = None
    changed_ns = 0
    for event in case.events:
        _ = store.emit("fixture_event", fixture_sequence=event.sequence, fixture_type=event.kind)
        match event.kind:
            case "run_started":
                if event.task is None or event.attempt_id is None:
                    raise InputError("replay", "missing late attempt identity")
                late = store.start(event.task, initial, tuple(store.artifacts[-1:]), "late", event.attempt_id)
            case "requirements_changed":
                changed_ns = store.revise(case.target)
            case "run_completed":
                if late is None:
                    raise InputError("replay", "late completion without start")
                _ = store.complete(late)
            case _:
                raise InputError("replay", f"unsupported event {event.kind}")
    if not changed_ns or store.active:
        raise InputError("replay", "replay incomplete")
    return changed_ns
