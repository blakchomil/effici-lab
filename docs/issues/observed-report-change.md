# Collect an observed report-change request and test deterministic interpretation controls

## Problem

The two current studies use structured development changes. B1/B2 already reach the
execution-count minimum, so they do not demonstrate a need for an AI policy. We need a
real report-change request and a controlled check of whether simple interpretation plus
clarification is sufficient.

## Work

Collect one naturally occurring request to change this project's report or experiment
artifact. Preserve the request verbatim with its date, source, relevant prior report,
input hashes, and publication permission/redactions. A maintainer's actual request is
eligible, but must be identified as such; do not present it as external use or an observed
failure unless a failure was actually recorded. Existing bounded examples can be inputs
only when their provenance meets these requirements.

Before running comparisons, record the intended requirement and acceptable interpretations.
For ambiguity, ask a concrete clarification and preserve the answer; an unanswered question
remains unresolved. Keep semantic requirements separate from whether the current renderer
can express them.

Run the same case through a deterministic interpretation rule plus B1/B2 and a clarification
control plus B1/B2. Give both the same request/context, clarification access, artifact history,
checks, and execution permissions. Use B0 with the confirmed requirement as the recomputation
reference. Evaluate output independently from the policy, and distinguish interpretation
errors from reuse/planning errors. Record costs of interpretation, questions, checks,
transformations, reruns, and fallback. No additional paid API calls are needed.

## Acceptance criteria

- [ ] A reviewable provenance record distinguishes observed text, supplied context,
  human-confirmed meaning, and any researcher-added fixtures.
- [ ] Deterministic and clarification controls are specified before comparison and executed
  with the same available information. Ambiguity is resolved or explicitly left unresolved.
- [ ] Exact commands, code/input hashes, exit codes, final outputs, assessments, and cost
  records are preserved under a new run ID; failures are retained.
- [ ] Independent output checks report validity and actual invalid reuse for every control.
  Unsupported output capabilities are identified separately from interpretation failures.
- [ ] A conclusion names the observed gap, or explicitly records that simple controls suffice
  and no AI comparison is justified by this case.

## Failure criterion and stopping rule

A baseline fails this case only if a reproducible execution violates the confirmed output
contract, consumes an invalid artifact, or exceeds a preregistered cost bound under equal
information and permissions. An initial parsing miss fixed by permitted clarification is
not a residual baseline failure. A missing renderer feature alone is not an AI opportunity.
If the controls produce valid outputs at the finite execution-count minimum, retain that
negative result and close the case without adding an AI policy. Report other cost dimensions
separately; an unresolved request cannot establish policy superiority.
