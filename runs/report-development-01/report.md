# Report workflow follow-up

Actual input: preserved Phase 1 metrics. Change variants are proposed development cases.
Workflow: select cases -> summarize policy evidence -> render Markdown.
No original experiment, AI policy, hidden benchmark or remote worker was executed.

| Change | Policy | Valid final | New report stages | Reference minimum | Cache exposures | Invalid cache uses | Policy ms |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Title change | B0 | True | 3 | 1 | 0 | 0 | 2.301 |
| Column order change | B0 | True | 3 | 1 | 0 | 0 | 2.268 |
| D4/D5 evidence selection | B0 | True | 3 | 3 | 0 | 0 | 2.131 |
| Return to original | B0 | True | 3 | 0 | 0 | 0 | 2.779 |
| Title change | B1 | True | 1 | 1 | 4 | 0 | 1.777 |
| Column order change | B1 | True | 1 | 1 | 4 | 0 | 2.038 |
| D4/D5 evidence selection | B1 | True | 3 | 3 | 0 | 0 | 2.910 |
| Return to original | B1 | True | 0 | 0 | 6 | 0 | 1.395 |
| Title change | B2 | True | 1 | 1 | 4 | 0 | 2.317 |
| Column order change | B2 | True | 1 | 1 | 4 | 0 | 2.513 |
| D4/D5 evidence selection | B2 | True | 3 | 3 | 0 | 0 | 2.676 |
| Return to original | B2 | True | 0 | 0 | 6 | 0 | 1.777 |

## Interpretation

Both strong deterministic baselines reached the current-cache execution-count bounds.
An additional AI policy is not justified by a remaining gap in these cases.
Phase 2 AI comparison, Phase 3 natural-language evaluation and Phase 4 integration remain uncompleted.

## Accounting and limits

Common initial report generation: 3 stages, measured once and cloned.
Original Phase 1 experiment reruns: 0. Original measurements are reused as input, not claimed as avoided compute.
B2 contract checks regenerate expected role content; they perform computation and are timed.
Measured workflow hashes: hash_operations + 2 * key_computations; setup/evaluator hashes are outside that counter.
Per-operation times overlap decisions/checks/execution; do not add them as disjoint total cost.
One fixed-order synchronous stream per policy. These tiny timings do not establish stable speed savings.
All metrics rows and change variants are public development inputs. No held-out or model-isolation claim.
Unknown/malformed use is treated as unverified; this is not proof of universal reuse safety.
This is a bounded report API, not a generic workflow system or finished external adapter.

Evidence: manifest.json, source_metrics.json, metrics.json, initial/, B0/, B1/, B2/.
Each policy preserves revisions, attempts, artifacts, assessments and actual-use events.
