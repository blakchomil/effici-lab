# Contributing

effici-lab studies whether artifact revalidation can reduce unnecessary work after a
requirement changes, compared with strong deterministic baselines. Useful contributions
include reproducible failures, independent reproductions, clearer documentation, and
small fixes. Negative results are welcome.

Read [README.md](README.md), [RESEARCH.md](RESEARCH.md), [STATE.md](STATE.md), and
[AGENTS.md](AGENTS.md) before changing experiment behavior. Keep a contribution focused
on one question or defect; discuss a larger experiment in an issue first.

## Run and check

Use Python 3.13 or newer from the repository root. Runtime code uses the standard library.
Both commands create new run directories and preserve existing results:

```bash
python3 -m src.intent_revalidation
python3 -m src.intent_revalidation.report_workflow
```

Expected CLI summaries are `Final contracts satisfied: 15/15` and
`Report workflow contracts satisfied: 12/12`. Each command prints its report path.
Use `--help` for input/output options. The second workflow reads the committed Phase 1
metrics; it does not rerun the original experiment.

Install the locked development environment and run the checks:

```bash
uv sync --locked --group dev
uv run pytest -q
uv run ruff check src tests examples
uv run ruff format --check src tests examples
uv run basedpyright
```

Reproduce the observed-request interface probe with a new output directory:

```bash
PYTHONPATH=. python3 examples/support-readiness/probe.py /tmp/my-new-readiness-run
```

Its exit 0 confirms the documented bounded observations, including unsupported readiness fields;
it does not mean a support application is ready. Historical probe snapshots are retained as evidence
and excluded from live-source lint/type checks.

For a pull request, explain the problem, changed behavior, exact validation commands,
and remaining limitations. Add a regression test for a meaningful failure when changing
behavior. Preserve old runs; record new results under a new run ID.

## Report a reproduction or failure

Open an [issue](https://github.com/blakchomil/effici-lab/issues) with:

- Commit SHA, whether the checkout was modified, OS/architecture, Python and uv versions.
- Exact commands, exit codes, full stdout/stderr, and expected versus observed behavior.
- New run IDs and the resulting `manifest.json`, `metrics.json`, and `report.md`.
  Include relevant event/artifact records or an archive when diagnosing a discrepancy.
- Test/static-check results, including failures; sanitize private paths or data and document
  any redactions that prevent exact reproduction.
- Who performed the run and their relationship to the project, plus any setup friction.
  State whether assistance or automation was used.

A fresh clone or CI run is useful execution evidence. An independent external reproduction
requires a person outside the implementation effort to run and report it; a maintainer's
agent or hosted CI job does not establish external use. A reproduction alone also does
not establish usefulness in another workflow.

Maintainers will reproduce the report where possible, ask for missing inputs, and record
whether it is a bug, documentation gap, research limitation, or already covered case.
There is no guaranteed response or resolution time.

## Research changes

Record the observed request and distinguish it from an invented development example.
Give B0/B1/B2 the same input information, cache history, tools, and execution permissions.
Measure checks, interpretation, clarification, transformations, reruns, and fallback costs.
Do not infer total-cost savings from fewer stage executions, or AI superiority from these
public development cases. Additional paid API experiments are outside the current scope.

Contributions are distributed under the repository's [MIT license](LICENSE).
