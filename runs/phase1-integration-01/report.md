# Phase 1: local deterministic comparison

Public development cases, one run per case/policy. No AI policy or held-out evaluation.

B0 executes all stages. B1 searches all historical granular keys and checks byte integrity. B2 executes role-specific content checks before reuse. Each starts from the same copied initial cache; activation cache manifests were compared byte-for-byte.

## Observed outcomes

| Case | Policy | Final valid | New executions | Reference min | Excess | Reuse links | Semantic checks | Integrity checks | Late executions | Invalid cache use / cache exposures |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| D1 | B0 | True | 4 | 1 | 3 | 0 | 0 | 0 | 0 | 0 / 0 |
| D1 | B1 | True | 1 | 1 | 0 | 3 | 0 | 3 | 0 | 0 / 4 |
| D1 | B2 | True | 1 | 1 | 0 | 3 | 4 | 0 | 0 | 0 / 4 |
| D2 | B0 | True | 4 | 2 | 2 | 0 | 0 | 0 | 0 | 0 / 0 |
| D2 | B1 | True | 2 | 2 | 0 | 2 | 0 | 2 | 0 | 0 / 3 |
| D2 | B2 | True | 2 | 2 | 0 | 2 | 4 | 0 | 0 | 0 / 3 |
| D3 | B0 | True | 4 | 0 | 4 | 0 | 0 | 0 | 0 | 0 / 0 |
| D3 | B1 | True | 0 | 0 | 0 | 4 | 0 | 4 | 0 | 0 / 5 |
| D3 | B2 | True | 0 | 0 | 0 | 4 | 4 | 0 | 0 | 0 / 5 |
| D4 | B0 | True | 4 | 1 | 3 | 0 | 0 | 0 | 1 | 0 / 0 |
| D4 | B1 | True | 1 | 1 | 0 | 3 | 0 | 3 | 1 | 0 / 4 |
| D4 | B2 | True | 1 | 1 | 0 | 3 | 3 | 0 | 1 | 0 / 4 |
| D5 | B0 | True | 4 | 1 | 3 | 0 | 0 | 0 | 1 | 0 / 0 |
| D5 | B1 | True | 1 | 1 | 0 | 3 | 0 | 3 | 1 | 0 / 4 |
| D5 | B2 | True | 1 | 1 | 0 | 3 | 4 | 0 | 1 | 0 / 4 |

## Actual time (milliseconds)

Measured with perf_counter_ns, including history/artifact I/O in the wall windows. Order B0/B1/B2 is fixed; these tiny single-sample timings are not a speed benchmark.

| Case | Policy | Initial compute | Late compute | New compute | Semantic checks | Integrity checks | Binding | First valid result after change | All remaining work quiescent | Policy wall | Evaluator/reference overhead |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| D1 | B0 | 1.459 | 0.000 | 0.707 | 0.000 | 0.000 | 0.205 | 2.834 | 2.882 | 2.511 | 2.633 |
| D1 | B1 | 1.459 | 0.000 | 0.207 | 0.000 | 0.114 | 0.382 | 2.184 | 2.255 | 2.038 | 1.843 |
| D1 | B2 | 1.459 | 0.000 | 0.191 | 0.494 | 0.000 | 0.190 | 2.142 | 2.197 | 2.023 | 1.794 |
| D2 | B0 | 0.648 | 0.000 | 0.704 | 0.000 | 0.000 | 0.216 | 2.640 | 2.736 | 2.576 | 1.381 |
| D2 | B1 | 0.648 | 0.000 | 0.345 | 0.000 | 0.045 | 0.217 | 1.953 | 2.005 | 1.847 | 1.095 |
| D2 | B2 | 0.648 | 0.000 | 0.335 | 0.350 | 0.000 | 0.187 | 2.470 | 2.521 | 2.355 | 1.109 |
| D3 | B0 | 0.658 | 0.000 | 0.731 | 0.000 | 0.000 | 0.204 | 2.608 | 2.663 | 2.507 | 1.329 |
| D3 | B1 | 0.658 | 0.000 | 0.000 | 0.000 | 0.103 | 0.203 | 1.196 | 1.248 | 1.074 | 0.934 |
| D3 | B2 | 0.658 | 0.000 | 0.000 | 0.614 | 0.000 | 0.192 | 1.695 | 1.741 | 1.557 | 0.891 |
| D4 | B0 | 0.341 | 0.222 | 0.777 | 0.000 | 0.000 | 0.238 | 3.493 | 3.552 | 2.938 | 1.607 |
| D4 | B1 | 0.341 | 0.172 | 0.164 | 0.000 | 0.065 | 0.192 | 1.787 | 1.844 | 1.349 | 1.120 |
| D4 | B2 | 0.341 | 0.176 | 0.187 | 0.534 | 0.000 | 0.245 | 2.577 | 2.642 | 2.118 | 1.258 |
| D5 | B0 | 0.524 | 0.172 | 0.690 | 0.000 | 0.000 | 0.216 | 3.145 | 3.201 | 2.662 | 4.364 |
| D5 | B1 | 0.524 | 0.171 | 0.174 | 0.000 | 0.094 | 0.215 | 2.084 | 2.136 | 1.565 | 2.088 |
| D5 | B2 | 0.524 | 0.178 | 0.151 | 0.491 | 0.000 | 0.202 | 2.494 | 2.543 | 1.937 | 1.854 |

## What was actually selected

- D1/B0: load:rerun, normalize:rerun, aggregate:rerun, render:rerun. [Actual report](D1/B0/artifacts/a-policy-render-000029.html)
- D1/B1: load:reuse, normalize:reuse, aggregate:reuse, render:rerun. [Actual report](D1/B1/artifacts/a-policy-render-000021.html)
- D1/B2: load:reuse, normalize:reuse, aggregate:reuse, render:rerun. [Actual report](D1/B2/artifacts/a-policy-render-000022.html)
- D2/B0: load:rerun, normalize:rerun, aggregate:rerun, render:rerun. [Actual report](D2/B0/artifacts/a-policy-render-000029.md)
- D2/B1: load:reuse, normalize:reuse, aggregate:rerun, render:rerun. [Actual report](D2/B1/artifacts/a-policy-render-000024.md)
- D2/B2: load:reuse, normalize:reuse, aggregate:rerun, render:rerun. [Actual report](D2/B2/artifacts/a-policy-render-000026.md)
- D3/B0: load:rerun, normalize:rerun, aggregate:rerun, render:rerun. [Actual report](D3/B0/artifacts/a-policy-render-000029.md)
- D3/B1: load:reuse, normalize:reuse, aggregate:reuse, render:reuse. [Actual report](D3/B1/artifacts/a-initial-render-000009.md)
- D3/B2: load:reuse, normalize:reuse, aggregate:reuse, render:reuse. [Actual report](D3/B2/artifacts/a-initial-render-000009.md)
- D4/B0: load:rerun, normalize:rerun, aggregate:rerun, render:rerun. [Actual report](D4/B0/artifacts/a-policy-render-000028.html)
- D4/B1: load:reuse, normalize:reuse, aggregate:reuse, render:rerun. [Actual report](D4/B1/artifacts/a-policy-render-000020.html)
- D4/B2: load:reuse, normalize:reuse, aggregate:reuse, render:rerun. [Actual report](D4/B2/artifacts/a-policy-render-000020.html)
- D5/B0: load:rerun, normalize:rerun, aggregate:rerun, render:rerun. [Actual report](D5/B0/artifacts/a-policy-render-000031.html)
- D5/B1: load:reuse, normalize:reuse, aggregate:reuse, render:rerun. [Actual report](D5/B1/artifacts/a-policy-render-000023.html)
- D5/B2: load:reuse, normalize:reuse, aggregate:reuse, render:rerun. [Actual report](D5/B2/artifacts/a-policy-render-000024.html)

## Cost and validity interpretation

The lower bound enumerates all existing-candidate/fresh-stage plans, validates cached content with an independent source-derived oracle, and checks selected input hashes. It uses one unit per stage execution. This is a count lower bound for the four allowed operations, not an optimum over elapsed time, checks, inference, dollars, or arbitrary transformations.

Initial computations are performed once per case and cloned, so the repeated initial columns are shared costs, not additional policy work. D4/D5 perform one real late computation per policy after the change. Replay preserves start/change/complete order but does not reproduce asynchronous worker cancellation. No prior CPU duration is invented; no sleep or weighted workload was added.

New rendering is counted as computation, including format conversion. Checks, cache comparisons, decisions and binding costs are measured in metrics.json. Inner key/check timings overlap the decision duration; they must not be summed twice. Total wall time runs from requirements_changed through work_quiescent. Independent evaluator/reference overhead occurs afterward and is separately measured. No model calls, tokens, remote API charges, retries or cancellation occur. Local resource cost in dollars is unestimated.

The audit checks every consumption, binding and publication for r1, not just the final pointer. Cache exposures include repeated use/bind/publication events; each denominator is shown. Invalid/unknown candidates rejected during B2 inspection are not counted as actual invalid reuse or as a prior reuse proposal. The implementation emits no reuse proposal before inspection; incorrect reuse proposals are zero in these cases.

## Conclusion and limits

Inspect the observed table before drawing a conclusion. If B1/B2 reach the count lower bound with valid results, these development cases leave no demonstrated gap for an AI policy. That is a useful negative finding, not evidence of AI superiority or general safety. Six synthetic rows, five public structured changes, a linear graph and trusted generated provenance are the scope. Natural-language interpretation, unknown contracts, other workflows, parallel failures and unseen changes remain untested.

Next research decision: identify one representative real change that these strong baselines cannot already solve before spending on Phase 2 model evaluation.
