# Observed request and report-interface coverage probe

This case starts from the user's actual support-readiness critique and follow-up
in [request.md](request.md). The proposed report transformation is explicitly an
agent interpretation, not a user quotation. The historical baseline facts are
in [repository-snapshot.json](repository-snapshot.json).

The complete user request concerns licensing, maintenance, and evidence of useful
research. This probe handles only the report-coverage research slice. Passing it
does not add a license, create maintenance history, or complete an application.

From the repository root, use a new output directory:

```sh
PYTHONPATH=. uv run examples/support-readiness/probe.py /tmp/support-readiness-probe-01
```

The probe consumes the actual preserved Phase 1 metrics, creates an initial
report, and asks B1 to change its title to `Support readiness`. It records the
real operation counts, timing, byte hashes, artifact provenance, audit, and
resulting report. It also attempts to construct the proposed readiness columns
through the existing public `Column` enum and records the rejection errors.

Exit 0 means the bounded observations match: the title change remains valid
under the existing report contract, two stages are reused, one is executed,
and the three proposed columns are unsupported. It does **not** mean the output
satisfies a support-readiness assessment: the report still contains experiment
totals and cannot derive licensing or maintenance facts from those totals.

## Simpler alternative and conclusion

A deterministic checklist supplied with the separately observed repository facts
can already report that the historical revision lacked a root license file,
had six commits and successful CI, and had no issues/PRs/releases in the returned
lists. It must leave the need for AI credits unestablished. The snapshot's
`interpretation` records that bounded assessment without a model call.

The missing inputs and output vocabulary are a coverage limit of this small
workflow. They are not evidence that granular caching or deterministic contracts
fail on the same well-specified task. Adding the needed inputs and a template is
a straightforward alternative to evaluate before adding an AI reuse policy.

No claim is made about saved human time, API-cost savings, external reproduction,
natural-language interpretation accuracy, or generalization. Runtime timing is
one local observation, not an end-to-end comparison including agent development.
The snapshot deliberately stays at the pre-change revision even if the live
repository gains a license, issues, or a release later in this turn.

## Captured execution

[observed-02/result.json](runs/observed-02/result.json) records exit-0 observations:
the initial report used three stages; the B1 title revision executed one stage
and reused two. The audit found zero invalid-use events. All three proposed
readiness columns were rejected. The resulting
[report](runs/observed-02/retitled-report.md) still shows only experiment metrics.
[verification.json](runs/observed-02/verification.json) records the actual CLI,
strict lint/type checks, and the rejected overwrite attempt.

`observed-01` retains the earlier runtime result and its code snapshot before
static-check fixes. The final `observed-02` probe took about 13 ms locally;
that measurement excludes implementation work and is not a savings comparison.

## Subsequent human confirmation and full report

The human subsequently confirmed preserving prior numbers/sources and reporting current support
facts and missing evidence. [clarification-20261010.json](clarification-20261010.json) preserves the
exact question/options/response. This is elicited maintainer confirmation, not external feedback
or a held-out natural-language target. The earlier request and probe retain their historical boundary.

[Current frozen facts](current-facts-20261010.json) concern revision
`5066fa41e5d4cde50322f3795437c0565cfc8163`. [Capture evidence](evidence-20261010.json) contains
actual read-only commands, outputs and timings. The old pre-license snapshot is unchanged.
[The protocol](protocol-20261010.md) specifies controls and checks before comparison.

```sh
python3 -m src.intent_revalidation.readiness_workflow
```

[Final results](../../runs/readiness-20261010-01/report.md): 25/25 repeated contracts, B0 four new
stages versus B1/B2 one composition and three reused numeric stages, invalid reuse 0/140 exposures.
Rule/clarification labels use the same exact-choice parser; this tests a clarified deterministic
workflow rather than distinct natural-language strategies. Simple controls suffice. Independent
numeric checks, exact-byte preservation and input/code/environment provenance are audited.

Input/seed, clone, runtime and evaluator costs are separate. Replay generates no new human question.
Human waiting/repair, development-agent costs and local dollar costs remain unknown. No evaluated
model or paid API was used. External usefulness remains open.
`readiness-development-20261010-01` retains an input-path capture failure before any arm ran;
`readiness-development-20261010-02` retains the succeeding run before audit refinements.
