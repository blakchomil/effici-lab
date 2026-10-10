"""Retrospective audit of every actual use and publication, including stale overwrites."""

from dataclasses import dataclass

from .evaluation import evaluate
from .fixtures import string
from .model import ROLES, Artifact, ArtifactId, Json, Revision, Validity
from .storage import Store


@dataclass(frozen=True, slots=True)
class Audit:
    """Separate actual invalid use, invalid cache reuse and the whole publication history."""

    final_satisfied: bool
    publication_count: int
    invalid_publications: int
    actual_use_events: int
    invalid_use_events: int
    cache_use_events: int
    invalid_reuse_events: int
    invalid_reuse_artifacts: int
    first_valid_ns: int | None

    def to_json(self) -> Json:
        return {
            "final_satisfied": self.final_satisfied,
            "publication_count": self.publication_count,
            "invalid_publications": self.invalid_publications,
            "actual_use_events": self.actual_use_events,
            "invalid_use_events": self.invalid_use_events,
            "cache_use_events": self.cache_use_events,
            "invalid_reuse_events": self.invalid_reuse_events,
            "invalid_reuse_artifacts": self.invalid_reuse_artifacts,
            "first_valid_ns": self.first_valid_ns,
        }


def audit_history(store: Store, target: Revision) -> Audit:
    """Score the entire target-revision event stream rather than just its final pointer."""
    artifacts = {artifact.id: artifact for artifact in store.artifacts}
    checks = {
        identifier: evaluate(artifact, target.requirements, store.context)
        for identifier, artifact in artifacts.items()
    }
    for identifier, check in checks.items():
        artifact = artifacts[identifier]
        store.append(
            "audit_assessments.jsonl",
            {
                "artifact_id": identifier,
                "target_revision_id": target.id,
                "consumer_role": ROLES[artifact.task],
                "validity": check.validity.value,
                "reason": check.reason,
            },
        )
    uses = invalid = cache_uses = bad_reuses = publications = bad_publications = 0
    first_valid: int | None = None
    invalid_ids: set[ArtifactId] = set()
    last_publication_valid = False
    for event in store.events:
        if event.get("revision_id") != target.id or event["type"] not in {
            "artifact_consumed",
            "artifact_bound",
            "report_published",
        }:
            continue
        identifier = ArtifactId(string(event["artifact_id"]))
        artifact = artifacts[identifier]
        valid = checks[identifier].validity is Validity.VALID
        valid = valid and event["consumer_role"] == ROLES[artifact.task]
        uses += 1
        invalid += int(not valid)
        cached = event["from_cache"] is True
        cache_uses += int(cached)
        if cached and not valid:
            bad_reuses += 1
            invalid_ids.add(identifier)
        if event["type"] == "report_published":
            publications += 1
            bad_publications += int(not valid)
            last_publication_valid = valid
            timestamp = event["monotonic_ns"]
            if valid and first_valid is None and isinstance(timestamp, int):
                first_valid = timestamp
    satisfied = last_publication_valid and bad_publications == 0 and invalid == 0
    return Audit(
        satisfied,
        publications,
        bad_publications,
        uses,
        invalid,
        cache_uses,
        bad_reuses,
        len(invalid_ids),
        first_valid,
    )


def cache_fingerprint(cache: tuple[Artifact, ...]) -> Json:
    return [
        {
            "task_id": item.task.value,
            "sha256": item.sha256,
            "cache_key": item.cache_key,
            "input_hashes": list(item.input_hashes),
            "revision_id": item.revision_id,
        }
        for item in cache
    ]
