# effici-lab

Research on artifact revalidation and selective reruns after requirement changes.

**Research question:** After a user changes a requirement, can an agent use artifact provenance and executable checks to reuse existing work more efficiently than strong deterministic methods, while preserving correctness?

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

## Result layout

- `manifest.json`, `source.csv`, `dev_cases.json`, `code_snapshot/`: exact execution inputs and implementation.
- `<case>/initial/`: common initial artifacts and measured execution history.
- `<case>/<policy>/artifacts/`: immutable actual CSV-derived JSON and rendered reports.
- `events.jsonl`, `attempts.jsonl`, `artifacts.jsonl`, `revisions.jsonl`: observed histories in each workspace.
- `assessments.jsonl`: policy inspections where a policy performs them.
- `audit_assessments.jsonl`, `activation_cache.json`, `current.json`, `metrics.json`: independent assessments, fair cache and selected output.
- Root `report.md`, `metrics.json`, `verification.json`, `verification-tests.xml`: comparison and validation evidence.

## Development checks

Development tools are isolated in the local uv environment. Runtime code uses only the standard library.
The project's explicit choices are argparse for the CLI, dataclasses/manual boundary parsing, and pytest for tests.

```bash
uv sync --group dev
uv run pytest -q
uv run ruff check src tests
uv run ruff format --check src tests
uv run basedpyright
```

Recorded result: **46 tests passed**, Ruff and formatting passed, zero type diagnostics.
Tests cover content corruption, wrong period/unit/source/format, incomplete snapshots,
cache provenance changes, older cache matches, stale overwrites, event order and cost accounting.
The CLI was also driven through its help, success, missing-input and existing-output paths.

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
Natural-language interpretation, unseen changes, other workflows, parallel failures and recovery remain untested.
A task failure leaves partial failure history and aborts the experiment; comparison across failing workflows is not implemented.

Before Phase 2, identify one representative real change that strong baselines cannot already solve.
AI advantage, novelty and usefulness beyond this local scope remain unestablished.

## Open source and support

The long-term goal is to build a useful open-source research project and apply for OpenAI open-source support.
The research success criterion remains the question above, not program acceptance.

As checked on 2026-10-10 KST, [Codex for Open Source](https://developers.openai.com/community/codex-for-oss)
supports maintainers and reviews usage, ecosystem importance and active maintenance.
The [application form](https://openai.com/form/codex-for-oss/) requires a public repository URL.
Repository creation is appropriate at this stage, but application readiness also needs a credible account of utility and maintenance.
Those are program criteria, not evidence that this project will be accepted.

The current state is a local Git repository with no commits or remote.
A GitHub repository name can differ from the Mac folder name.
The public name and release license have not been chosen.

## Prior-art boundary

The starter's prior-art discussion and dated sources are preserved in [RESEARCH.md](RESEARCH.md).
Incremental execution, provenance, requirement tracking and selective reruns alone are not claimed as new inventions.
No third-party implementation was copied into this project.
