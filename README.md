# effici-lab

Research on artifact revalidation and selective reruns after requirement changes.

**Research question:** After a user changes a requirement, can an agent use artifact provenance and executable checks to reuse existing work more efficiently than strong deterministic methods, while preserving correctness?

The intended use is handling revisions to an agent's work: keep verified analysis when a report title changes,
recompute the affected stages when the evidence selection changes, and explain those decisions with records.
The current implementation is a local comparison harness. Reliable natural-language understanding and
an AI policy's advantage over deterministic methods remain research questions.

한국어 연구 계획: [RESEARCH.md](RESEARCH.md) · 실제 상태: [STATE.md](STATE.md)

## Current result

Phase 1 is implemented and was run locally on an Apple Silicon Mac on 2026-10-10 KST.
This is a **public development experiment**, with six synthetic CSV rows and five structured change cases.
It is not a held-out benchmark. No AI policy was evaluated.

[Actual comparison report](runs/phase1-20261010-01/report.md) ·
[Metrics](runs/phase1-20261010-01/metrics.json) ·
[Code/data/environment manifest](runs/phase1-20261010-01/manifest.json) ·
[Verification](runs/phase1-20261010-01/verification.json)

| Policy | Valid final results | New stage executions | Semantic checks | Byte integrity checks | Actual invalid cache use |
| --- | ---: | ---: | ---: | ---: | ---: |
| B0: full recomputation | 5/5 | 20 | 0 | 0 | 0 |
| B1: granular keys and historical cache | 5/5 | 5 | 0 | 15 | 0/20 cache exposure events |
| B2: executable role contracts | 5/5 | 5 | 19 | 0 | 0/20 cache exposure events |

The per-case minimum new executions were 1, 2, 0, 1, 1. B1 and B2 reached those execution-count bounds.
There is no observed gap here that requires AI. Fewer executions do not establish lower total cost or general safety.
B2 incurs semantic verification costs; all measured times, bindings, decisions and initial/late work are in the results.

## Run locally

Python 3.13+ is the only runtime requirement. Clone the repository and run from its root:

```bash
git clone https://github.com/blakchomil/effici-lab.git
cd effici-lab
python3 -m src.intent_revalidation
python3 -m src.intent_revalidation --help
```

The default command creates a unique `runs/<KST timestamp>-<random id>/` directory.
For an explicit ID, use `--run-id my-run`. Existing directories are rejected; previous runs are preserved.
Use `--cases path/to/dev_cases.json` or `--output path/to/runs` to select input/output locations.

The exact recorded final invocation was:

```bash
python3 -m src.intent_revalidation --run-id phase1-20261010-01
```

It exited 0 and reported `Final contracts satisfied: 15/15`.
The earlier `phase1-integration-01` run is preserved with its own code snapshot.

## What executes

`load CSV → normalize → aggregate → render report`

- D1 changes Markdown to HTML.
- D2 changes January to February.
- D3 creates a new revision without changing structured semantics.
- D4 completes an r0 aggregate after an HTML change; it remains reusable after assessment.
- D5 completes an r0 Markdown report after an HTML change; it is preserved but never published as the r1 result.

Each case has one measured initial seed, copied into each isolated policy workspace.
D4/D5 then execute real late work in the specified start/change/complete replay order.
The policies activate only after the replay completes. This is synchronous local replay, not remote parallel cancellation.

The source bytes, code, environment and contract version are fingerprinted.
Requirement revision, logical task, run attempt, artifact, assessment and event records retain separate identities.
Artifacts are written exclusively to unique files; only `current.json` is a mutable result pointer.

B1 searches all historical keys based on relevant requirement fields and actual input bytes.
B2 checks bytes, provenance, selected input linkage and role content. All policies have the same cache and tools.
The evaluator independently parses the CSV and actual Markdown/HTML output.
It audits every target-revision consumption, binding and publication, including later stale overwrites.
The reference enumerates current-cache/fresh-stage combinations with unit execution costs; it never feeds answers into policy selection.

## Follow-up: this project's report artifacts

A second local workflow reads the **preserved, actual Phase 1 metrics**:

`select cases → summarize policy evidence → render Markdown`

```bash
python3 -m src.intent_revalidation.report_workflow
python3 -m src.intent_revalidation.report_workflow --help
```

It creates a unique report run. `--metrics`, `--output` and `--run-id` select paths and identity.
The source experiment is not rerun. The four proposed development changes are title, column order,
D4/D5-only evidence, and return to the original requirements. They were motivated by our reporting work;
they are not a recorded field study or hidden evaluation.

The policies share one measured three-stage seed, then retain their own sequential cache histories.
B1 uses role-specific requirement fields and stage dependency fingerprints; B2 checks executable contracts.
An independent evaluator reconstructs expectations from the original metrics bytes, checks every intermediate
and rendered output, and audits actual binding, consumption and publication. Exhaustive reference planning
is performed after policy execution and does not supply policy answers.

This is the Phase 2 entry study. AI comparison, natural-language evaluation and external integration
are still conditional on a concrete problem and measured benefit. Additional paid API calls are excluded
under the user's current research constraint.

[Actual follow-up report](runs/report-followup-20261010-02/report.md) ·
[Metrics](runs/report-followup-20261010-02/metrics.json) ·
[Manifest](runs/report-followup-20261010-02/manifest.json) ·
[Verification](runs/report-followup-20261010-02/verification.json)

| Change | B0 new stages | B1 new stages | B2 new stages | Execution-count minimum |
| --- | ---: | ---: | ---: | ---: |
| Title | 3 | 1 | 1 | 1 |
| Column order | 3 | 1 | 1 | 1 |
| D4/D5 only | 3 | 3 | 3 | 3 |
| Return to original | 3 | 0 | 0 | 0 |

All 12 final results were valid. B1/B2 each had zero invalid reuse events across 14 cache exposures.
Both matched the finite execution-count minimum. The original experiment was rerun zero times within
this study, and model calls/API charges were zero. Contract checks perform real recomputation and are
charged through counts and timing. These single-run millisecond measurements do not prove a total-cost advantage.

## Observed request: support-readiness evidence

The [observed request case](examples/support-readiness/README.md) preserves a real maintainer request
from this project's Codex conversation. The proposed readiness-report transformation is separately
labelled as an agent interpretation. A subsequent human clarification is preserved below.

```bash
PYTHONPATH=. python3 examples/support-readiness/probe.py /tmp/my-new-readiness-run
```

The measured probe reuses two stages and executes one to retitle an actual report. It also records
that licensing, maintenance and AI-credit fields are absent from the current report interface.
That capability gap does not establish failure of strong deterministic reuse methods or a need for AI.
A checklist with separately collected repository facts is a simpler alternative.
[Actual observations](examples/support-readiness/runs/observed-02/result.json) include counts, timing and hashes;
no human-time savings, external reproduction or model superiority is claimed.

### Human-clarified readiness report

The maintainer subsequently confirmed preserving prior numbers and sources while adding current
license/CI/prerelease facts and unestablished external reproduction and AI advantage.
[Actual question and answer](examples/support-readiness/clarification-20261010.json) ·
[Frozen dated facts](examples/support-readiness/current-facts-20261010.json) ·
[Protocol fixed before execution](examples/support-readiness/protocol-20261010.md)

```bash
python3 -m src.intent_revalidation.readiness_workflow
python3 -m src.intent_revalidation.readiness_workflow --help
```

The CLI replays frozen facts without live network/model calls. One measured new numeric seed,
byte-equal to the actual prior report, is cloned independently; this is a replay fixture,
not an imported production cache. New composition adds facts without changing numeric requirements.
Five cyclic repetitions of the **same public case** produced 25/25 valid outputs. Per repetition,
B0 regenerated four stages; B1/B2 reused three numeric stages and executed one composition,
matching the finite stage-count minimum. Invalid reuse was 0/140 actual cached exposures.
The rule/clarification labels share an exact-choice parser after human confirmation. They are
aliases, not independent natural-language algorithms. No AI policy was evaluated.

[Comparison report](runs/readiness-20261010-01/report.md) ·
[Example readiness document](runs/readiness-20261010-01/repeat-1/rule-B1/readiness-report.md) ·
[Metrics](runs/readiness-20261010-01/metrics.json) ·
[Manifest](runs/readiness-20261010-01/manifest.json) ·
[Verification](runs/readiness-20261010-01/verification.json)

Independent checks reconstruct numbers from original bytes, enforce exact embedded-byte preservation,
and audit all uses and composition-attempt provenance. B2's three role recomputations per run are
counted and timed as checks. Runtime, input/seed, clone and evaluator costs remain separate.
Human time, development-model usage and dollar costs are unmeasured. Millisecond repeats do not
establish stable or total-cost savings. Simple clarified controls suffice for this case.
The final local suite has 145 passing tests and strict checks. Historical probe records are unchanged.

## Result layout

- `manifest.json`, `source.csv`, `dev_cases.json`, `code_snapshot/`: exact execution inputs and implementation.
- `<case>/initial/`: common initial artifacts and measured execution history.
- `<case>/<policy>/artifacts/`: immutable actual CSV-derived JSON and rendered reports.
- `events.jsonl`, `attempts.jsonl`, `artifacts.jsonl`, `revisions.jsonl`: observed histories in each workspace.
- `assessments.jsonl`: policy inspections where a policy performs them.
- `audit_assessments.jsonl`, `activation_cache.json`, `current.json`, `metrics.json`: independent assessments, fair cache and selected output.
- Root `report.md`, `metrics.json`, `verification.json`, `verification-tests.xml`: comparison and validation evidence.

Stored absolute paths describe the original execution environment and are retained as historical provenance.
New runs write artifacts in the current checkout; the original paths need not exist on another machine.

## Development checks

Development tools are isolated in the local uv environment. Runtime code uses only the standard library.
The project's explicit choices are argparse for the CLI, dataclasses/manual boundary parsing, and pytest for tests.

```bash
uv sync --group dev
uv run pytest -q
uv run ruff check src tests examples
uv run ruff format --check src tests examples
uv run basedpyright
```

The preserved Phase 1 verification records **46 tests passed**, Ruff/formatting passed and zero type diagnostics.
Tests cover content corruption, wrong period/unit/source/format, incomplete snapshots,
cache provenance changes, older cache matches, stale overwrites, event order and cost accounting.
The CLI was also driven through its help, success, missing-input and existing-output paths.

The current follow-up verification records **77 tests passed**, with Ruff/formatting and type checks clean.
Additional tests exercise malformed metrics, wrong selection/source lineage, stage fingerprint scope,
independent detection of poisoned production stages, and invalid intermediate or stale publications.
Both real CLI workflows passed. The follow-up CLI rejected missing/malformed inputs, unsafe IDs and existing output.
Hosted [CI passed on Linux/Python 3.13 and macOS/Python 3.14](https://github.com/blakchomil/effici-lab/actions/runs/38029232478)
at commit `4a72806d06abc7fc1c97a9774a06ecd80352c673`: tests, static checks and both real CLI workflows.
The [CI receipt](runs/report-followup-20261010-02/ci-verification.json) retains the tested revision and job results.

Strict checks retain exhaustive variant handling and all substantive type diagnostics.
`reportUnnecessaryComparison` is disabled to permit the required exhaustive enum fallback.
Docstring exceptions apply to obvious methods/functions; structured InputError fields are exempt from bare-message style rules.
Automatic LSP diagnostics were unavailable in this session; the actual command-line type check passed.

## Limits and next research decision

One run per case/policy, fixed policy order, tiny synthetic data and trusted local instrumentation.
Recorded milliseconds are observations, not evidence of stable speed improvements.
Initial generation is shared, late execution is charged separately, and evaluator overhead is separated.
Inner check/key times overlap decision time; do not double-count them. Local resource cost in dollars is unestimated.

No process isolation from hidden answers is claimed. Public fixture expectations were available to the implementation agents.
The policy input record does not contain expected actions/totals, and evaluator results are used only afterward.
Natural-language interpretation, unseen changes, external workflows, parallel failures and recovery remain untested.
A task failure leaves partial failure history and aborts the experiment; comparison across failing workflows is not implemented.

Before adding an AI policy, identify one representative real change that strong baselines cannot already solve.
AI advantage, novelty and usefulness beyond this local scope remain unestablished.

## Open source and support

The long-term goal is to build a useful open-source research project and apply for OpenAI open-source support.
The research success criterion remains the question above, not program acceptance.

As checked on 2026-10-10 KST, [Codex for Open Source](https://developers.openai.com/community/codex-for-oss)
supports maintainers and reviews usage, ecosystem importance and active maintenance.
The [application form](https://openai.com/form/codex-for-oss/) requires a public repository URL.
Repository creation is appropriate at this stage, but application readiness also needs a credible account of utility and maintenance.
Those are program criteria, not evidence that this project will be accepted.

The public repository is [blakchomil/effici-lab](https://github.com/blakchomil/effici-lab), with `main` as its default branch.
The Phase 1 code, tests, fixtures and both recorded runs are published together.
A fresh clone was executed successfully on 2026-10-10 KST and satisfied all 15 final contracts.
Source and associated documentation are licensed under [MIT](LICENSE).
The [v0.1.0 development prerelease](https://github.com/blakchomil/effici-lab/releases/tag/v0.1.0)
tags the exact verified commit `27f0fda46379a7ed168a97346f84a11cb7793194`.
Its [verification receipt](docs/releases/v0.1.0-verification.json) records a fresh maintainer-agent clone,
77 passing tests, all three executable examples, and successful Linux/macOS CI at that revision.
See [CONTRIBUTING.md](CONTRIBUTING.md) for reproduction receipts and contributions, and
[CHANGELOG.md](CHANGELOG.md) for the initial development release scope.
The [support-readiness record](docs/support-readiness.md) separates implemented preparation from
unestablished external use, sustained maintenance and credit need.
Public next work: [confirmed requirements and controls](https://github.com/blakchomil/effici-lab/issues/1)
and [independent external reproduction](https://github.com/blakchomil/effici-lab/issues/2).

## Prior-art boundary

The starter's prior-art discussion and dated sources are preserved in [RESEARCH.md](RESEARCH.md).
Incremental execution, provenance, requirement tracking and selective reruns alone are not claimed as new inventions.
No third-party implementation was copied into this project.
