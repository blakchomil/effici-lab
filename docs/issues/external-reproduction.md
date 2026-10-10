# Obtain an independent external reproduction receipt for both workflows

## Problem

Maintainer/agent runs and Linux/macOS CI establish execution evidence, but they do not
establish reproduction by an independent external developer or usefulness outside this
project. Invite a person outside the implementation effort to run a fresh checkout and
report both successful steps and friction.

## Procedure

Follow [CONTRIBUTING.md](https://github.com/blakchomil/effici-lab/blob/main/CONTRIBUTING.md)
at a recorded commit. Run both documented CLIs and the locked uv checks. Use new run
directories and preserve logs. Assistance is allowed but must be disclosed; an agent-only
run or the maintainer's CI job does not satisfy the external-person requirement.

## Acceptance criteria

- [ ] An external person submits a public receipt identifying their relationship to the
  project and confirming that they performed the reproduction independently of its
  implementation effort. A public handle is sufficient; no private identity is required.
- [ ] The receipt records the commit SHA, checkout changes, OS/architecture, Python/uv
  versions, commands, exit codes, stdout/stderr, and any assistance or undocumented steps.
- [ ] Both new runs include manifests, metrics, reports, and enough artifact/event records
  to investigate discrepancies, attached or linked through a durable public location.
- [ ] The Phase 1 CLI reports 15/15 final contracts; the report CLI reports 12/12.
  Recorded policy execution counts are respectively B0/B1/B2 = 20/5/5 and 12/5/5,
  with zero invalid cache use for B1/B2. Timing values need not match.
- [ ] The locked development checks pass, or every failure has a linked investigation
  followed by a complete rerun of the affected scenario at a recorded revision.
- [ ] The maintainer reviews the submitted artifacts, records discrepancies and setup
  friction, and distinguishes reproduction from any separately reported real-world use.

## Failure criterion and stopping rule

The documented reproduction baseline fails if a supported fresh environment cannot
complete the commands as written, an expected contract/count/audit result differs, or a
development check fails. Preserve the original failure and diagnose it before rerunning;
do not replace its evidence with a success claim. Missing receipt artifacts or an
agent/CI-only run leave this issue open rather than satisfying external reproduction.

A successful receipt establishes one independent reproduction at one revision/environment.
It does not establish broad adoption, a maintenance track record, or AI superiority.
