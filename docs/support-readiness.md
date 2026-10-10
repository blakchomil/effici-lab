# Support-readiness evidence

Checked 2026-10-10 KST. The project's research goal is unchanged: assess artifact reuse after
requirement changes against strong deterministic alternatives. Program acceptance is not an experiment metric.

## What is concrete

- An [MIT license](../LICENSE) for the source and associated documentation.
- Two implemented local comparison workflows and preserved actual results: 15/15 and 12/12 final contracts.
- 163 passing local tests and strict checks; v0.1.0's 77 tests and successful Linux/macOS CI
  remain recorded separately at that release revision.
- [Contribution instructions](../CONTRIBUTING.md), reproducibility receipt requirements and initial release notes.
- A published [v0.1.0 development prerelease](https://github.com/blakchomil/effici-lab/releases/tag/v0.1.0)
  at exact verified revision `27f0fda46379a7ed168a97346f84a11cb7793194`, with
  [fresh-clone and CI verification](releases/v0.1.0-verification.json) attached as release assets.
- An [observed maintainer request](../examples/support-readiness/request.md) and
  [executed interface probe](../examples/support-readiness/runs/observed-02/result.json).

The observed probe exposes missing repository-fact inputs and readiness output fields. It does not
demonstrate that strong deterministic interpretation/reuse fails or that an AI policy would help.
The original request and researcher interpretation are separate. A fact-fed checklist remains a simple alternative.

A subsequent [human confirmation](../examples/support-readiness/clarification-20261010.json)
fixed that interpretation while preserving prior numbers/sources. The
[executed readiness comparison](../runs/readiness-20261010-01/report.md) has 25/25 valid repeated
outputs, B0 four versus B1/B2 one new stages each and invalid reuse 0/140 exposures. This is five
repeats of one public case; both interpretation labels share a confirmed-choice parser. Simple
clarified controls suffice. It does not demonstrate natural-language accuracy or the benefit of
asking a question. Actual attempt provenance and exact numeric-byte preservation are audited.

The subsequent [cache recovery comparison](../runs/recovery-20261010-01/report.md) preserves
original metrics and applies six between-revision local fault/change events in three cyclic
repetitions. All 54 current-revision audits passed. Per trace, full reruns used 18 stages and
B1/B2 each used 3; invalid reuse was 0/180 combined cached exposures. An independent stale
publication control was rejected despite restoring the final pointer. These injected public
development faults show bounded deterministic recovery, with measured verification overhead;
they do not establish real user incidents, restart safety, stable cost savings or AI necessity.

## What remains unestablished

- Independent reproduction by an external developer and usefulness in their own workflow.
- Sustained maintenance history or broad adoption.
- AI policy advantage, natural-language interpretation accuracy, stable total-cost savings or an API-credit need.
- Support-program eligibility or selection. No application has been submitted.

The [official application](https://openai.com/form/codex-for-oss/) asks about ecosystem qualification
and planned credit use. It includes coding and maintainer automation as uses. It does not make our
development results evidence of broad adoption or support acceptance.

## Next evidence

The [observed-request task](issues/observed-report-change.md) defines human-confirmed requirements,
equal-information deterministic/clarification controls, independent validity and cost checks.
The bounded human-confirmed case is now implemented; external usefulness remains unestablished.
The [external reproduction task](issues/external-reproduction.md) requires an actual external person;
maintainer agents, fresh checkouts and hosted CI do not satisfy that requirement.
Both tasks are publicly open as [#1](https://github.com/blakchomil/effici-lab/issues/1)
and [#2](https://github.com/blakchomil/effici-lab/issues/2), with observable acceptance and failure criteria.

No additional paid API calls are authorized in the current study. A future credit plan should identify
a specific unresolved question, a fixed evaluation protocol and a bounded call/token budget before any API run.
There is no current claim that AI is necessary for the measured cases.
