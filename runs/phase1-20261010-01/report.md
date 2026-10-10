# Phase 1: local deterministic comparison

Public development cases, one run per case/policy. No AI or held-out evaluation.

B0 executes every stage. B1 searches all historical granular keys and checks byte hashes. B2 checks executable role contracts before reuse. Each starts from the same copied cache. Activation cache manifests were compared byte-for-byte across all three policies.

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

Measured with perf_counter_ns. Wall windows include history and artifact I/O. Order B0/B1/B2 is fixed. These tiny single-sample timings are not a speed benchmark.

| Case | Policy | Initial compute | Late compute | New compute | Semantic checks | Integrity checks | Binding | First valid after change | All remaining work quiescent | Policy wall | Evaluator/reference overhead |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| D1 | B0 | 0.872 | 0.000 | 0.672 | 0.000 | 0.000 | 0.222 | 2.597 | 2.666 | 2.497 | 4.444 |
| D1 | B1 | 0.872 | 0.000 | 0.168 | 0.000 | 0.079 | 0.213 | 1.579 | 1.632 | 1.496 | 1.964 |
| D1 | B2 | 0.872 | 0.000 | 0.163 | 0.536 | 0.000 | 0.197 | 2.126 | 2.177 | 2.027 | 1.715 |
| D2 | B0 | 0.650 | 0.000 | 0.640 | 0.000 | 0.000 | 0.188 | 2.426 | 2.477 | 2.343 | 2.443 |
| D2 | B1 | 0.650 | 0.000 | 0.355 | 0.000 | 0.062 | 0.217 | 2.026 | 2.080 | 1.926 | 1.109 |
| D2 | B2 | 0.650 | 0.000 | 0.405 | 0.392 | 0.000 | 0.189 | 2.641 | 2.695 | 2.490 | 1.353 |
| D3 | B0 | 0.822 | 0.000 | 0.673 | 0.000 | 0.000 | 0.237 | 2.757 | 2.813 | 2.635 | 1.336 |
| D3 | B1 | 0.822 | 0.000 | 0.000 | 0.000 | 0.091 | 0.173 | 1.095 | 1.145 | 0.971 | 1.051 |
| D3 | B2 | 0.822 | 0.000 | 0.000 | 0.677 | 0.000 | 0.222 | 1.835 | 1.900 | 1.728 | 1.059 |
| D4 | B0 | 0.368 | 0.225 | 1.157 | 0.000 | 0.000 | 0.222 | 4.096 | 4.151 | 3.535 | 1.688 |
| D4 | B1 | 0.368 | 0.184 | 0.184 | 0.000 | 0.071 | 0.200 | 1.856 | 1.921 | 1.425 | 1.174 |
| D4 | B2 | 0.368 | 0.178 | 0.170 | 0.480 | 0.000 | 0.211 | 2.325 | 2.377 | 1.849 | 1.162 |
| D5 | B0 | 0.468 | 0.164 | 0.714 | 0.000 | 0.000 | 0.210 | 3.174 | 3.242 | 2.657 | 1.993 |
| D5 | B1 | 0.468 | 0.147 | 0.150 | 0.000 | 0.064 | 0.169 | 1.731 | 1.786 | 1.303 | 1.744 |
| D5 | B2 | 0.468 | 0.166 | 0.155 | 0.467 | 0.000 | 0.209 | 2.471 | 2.520 | 1.949 | 1.686 |

## Actual selections

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

The reference enumerates every existing-candidate/fresh-stage combination in the current cache. An independent CSV oracle checks candidate content and selected input hashes. Each execution costs one declared unit. This is a lower bound on the four-stage execution count. It is not an optimum over elapsed time, validation, inference, dollars or arbitrary transforms.

Initial computation runs once per case and is cloned; repeated initial columns are shared costs. D4/D5 execute one real late computation per policy after the requirement change. Replay preserves start/change/complete order but does not reproduce parallel cancellation. No historical CPU duration, artificial sleep or weighted workload was added.

New rendering, including format conversion, is counted as computation. Checks, key comparisons, decisions and bindings have counts and durations in metrics.json. Inner key/check time overlaps decision time and must not be added twice. Total wall time runs from requirements_changed through work_quiescent. Evaluator/reference overhead occurs afterward and is measured separately. There are no model calls, tokens, API charges, retries or cancellations. Local resource dollar cost is unestimated.

The audit checks every actual consumption, binding and publication under the target revision. Cache exposures count use/bind/publication events, including repeated exposure of one artifact. Rejected invalid/unknown candidates are distinct from actual invalid reuse. These policies emit no reuse proposal before inspection, so incorrect reuse proposals are zero.

## Conclusion and limits

- B0: 5/5 valid; 20 new executions.
- B1: 5/5 valid; 5 new executions.
- B2: 5/5 valid; 5 new executions.

Both strong baselines reach the execution-count lower bound with valid outputs. No added value of AI is established by this experiment. Scope: six synthetic rows, five public structured changes, linear graph and generated provenance. Unseen changes, natural-language interpretation, other workflows and parallel failures are untested. Zero observed invalid reuse is a finite development result, not a proof of general safety.

Next research decision: find one representative real requirement change that strong baselines cannot already solve before spending on Phase 2 model evaluation.
