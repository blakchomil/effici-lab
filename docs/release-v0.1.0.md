# effici-lab v0.1.0 — development research prerelease

An initial development prerelease of a reproducible research harness for deciding what artifacts to reuse after
requirements change. Python 3.13+ is required; runtime code uses only the standard
library. Source is available under the [MIT license](../LICENSE).

## Included workflows

- A four-stage CSV reporting workflow with five structured requirement-change cases,
  including late completion of work started under an earlier requirement revision.
- A three-stage report workflow over this project's preserved Phase 1 metrics, with
  title, column order, evidence selection, and return-to-original changes.
- B0 full recomputation, B1 granular historical caching, and B2 executable role contracts;
  immutable artifacts, provenance, event audits, and finite execution-count references.
- A preserved actual maintainer request with a bounded report-coverage probe. The title change
  reuses two stages and executes one; unsupported readiness fields are reported separately.

From the repository root:

```bash
python3 -m src.intent_revalidation
python3 -m src.intent_revalidation.report_workflow
PYTHONPATH=. python3 examples/support-readiness/probe.py /tmp/my-new-readiness-run
```

Each command creates a unique run directory and prints the report path. See
[CONTRIBUTING.md](../CONTRIBUTING.md) for development checks and reproduction receipts.

## Evidence

| Study | Final contracts | New stages: B0 / B1 / B2 | Recorded report |
| --- | ---: | ---: | --- |
| Phase 1, five changes | 15/15 | 20 / 5 / 5 | [Phase 1](../runs/phase1-20261010-01/report.md) |
| Report follow-up, four changes | 12/12 | 12 / 5 / 5 | [Report follow-up](../runs/report-followup-20261010-02/report.md) |

B1 and B2 reach the finite execution-count minimum in both studies. Their recorded
invalid cache use is 0/20 exposures each in Phase 1 and 0/14 each in the follow-up.
The studies perform no model calls or paid API calls. A reduction in stage executions
does not establish lower total cost: checks and decisions consume resources too.

[Local verification](../runs/report-followup-20261010-02/verification.json) records
77 passing tests, clean Ruff/format checks, and zero type diagnostics.
[Hosted CI](https://github.com/blakchomil/effici-lab/actions/runs/38029232478) passed tests,
static checks, and both CLIs on Linux/Python 3.13 and macOS/Python 3.14 at commit
`4a72806d06abc7fc1c97a9774a06ecd80352c673`. This is evidence for that tested revision;
the release tag's checks must be assessed separately.

## Scope and next questions

These are public development studies with tiny inputs, structured requirements, one
measurement per policy/case, trusted local instrumentation, and synchronous replay.
They are not a hidden benchmark or evidence of an AI policy's advantage. Natural-language
interpretation, external workflow utility, remote parallel recovery, and independent
external reproduction remain open. The [observed-request example](../examples/support-readiness/README.md)
separates the user's original request from an agent-derived report target. It identifies an interface
coverage limit and a simpler checklist alternative, not an AI advantage or generalization result.

The next work is to [collect an observed request and test interpretation/clarification
controls](issues/observed-report-change.md), and obtain an
[independent external reproduction receipt](issues/external-reproduction.md).
Neither maintenance duration nor outside adoption is established by this initial release.
