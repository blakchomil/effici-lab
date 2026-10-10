# Report workflow follow-up

Actual input: preserved Phase 1 metrics. Change variants are proposed development cases.
Workflow: select cases -> summarize policy evidence -> render Markdown.
No original experiment, AI policy, hidden benchmark or remote worker was executed.

| Change | Policy | Valid final | New report stages | Reference minimum | Cache exposures | Invalid cache uses | Policy ms |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Title change | B0 | True | 3 | 1 | 0 | 0 | 1.568 |
| Column order change | B0 | True | 3 | 1 | 0 | 0 | 1.580 |
| D4/D5 evidence selection | B0 | True | 3 | 3 | 0 | 0 | 1.544 |
| Return to original | B0 | True | 3 | 0 | 0 | 0 | 1.843 |
| Title change | B1 | True | 1 | 1 | 4 | 0 | 1.012 |
| Column order change | B1 | True | 1 | 1 | 4 | 0 | 0.981 |
| D4/D5 evidence selection | B1 | True | 3 | 3 | 0 | 0 | 1.505 |
| Return to original | B1 | True | 0 | 0 | 6 | 0 | 0.748 |
| Title change | B2 | True | 1 | 1 | 4 | 0 | 1.333 |
| Column order change | B2 | True | 1 | 1 | 4 | 0 | 1.406 |
| D4/D5 evidence selection | B2 | True | 3 | 3 | 0 | 0 | 1.854 |
| Return to original | B2 | True | 0 | 0 | 6 | 0 | 1.597 |

## Interpretation

Both strong deterministic baselines reached the current-cache execution-count bounds.
An additional AI policy is not justified by a remaining gap in these cases.
Phase 2 AI, Phase 3 language evaluation and Phase 4 integration are untested.

## Accounting and limits

Initial stages: 3; measured once and cloned.
Original Phase 1 reruns: 0. Reusing measurements does not measure avoided compute.
B2 checks regenerate expected content; this computation is timed.
Workflow hashes: hash_operations + 2 * key_computations.
Setup/evaluator hashes are excluded from the workflow hash counter.
Operation times overlap; adding them would double-count total cost.
One fixed-order stream per policy. Tiny timings cannot establish speed savings.
All inputs are public development cases. Held-out/model isolation is untested.
Unknown/malformed use is unverified. Universal reuse safety is unproven.
This bounded report API has no generic workflow or external adapter.

Evidence: manifest.json, source_metrics.json, metrics.json, initial/, B0/, B1/, B2/.
Policies preserve revisions, attempts, artifacts, assessments and actual uses.
