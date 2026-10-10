# Bounded recovery comparison

Independent current-revision audits satisfied: 54/54.

Public synthetic between-revision faults over unchanged actual Phase 1 metrics. Three cyclic policy orders repeat the same six-event trace; these are not independent user incidents or a process-restart study.

| Policy | Satisfied | New stages | Invalid reuse / cache exposures | Median policy wall (ms/event) | Contract checks | Integrity checks | Hashes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B0 | 18/18 | 54 | 0/0 | 1.5836875 | 0 | 0 | 108 |
| B1 | 18/18 | 9 | 0/90 | 1.0093335 | 0 | 60 | 66 |
| B2 | 18/18 | 9 | 0/90 | 1.4235205 | 84 | 0 | 174 |

| Repeat | Position | Event | Policy | New stages | Reference | Fault ms | Prep ms | Policy ms | Evaluation ms | Satisfied |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | E1 | B0 | 3 | 1 | 0.069 | 1.526 | 1.638 | 3.959 | True |
| 1 | 1 | E2 | B0 | 3 | 0 | 0.351 | 1.399 | 1.611 | 4.717 | True |
| 1 | 1 | E3 | B0 | 3 | 1 | 0.676 | 1.684 | 1.694 | 5.028 | True |
| 1 | 1 | E4 | B0 | 3 | 1 | 0.702 | 1.853 | 1.594 | 4.911 | True |
| 1 | 1 | E5 | B0 | 3 | 0 | 0.052 | 1.609 | 1.491 | 5.939 | True |
| 1 | 1 | E6 | B0 | 3 | 0 | 0.245 | 1.729 | 1.491 | 6.850 | True |
| 1 | 2 | E1 | B1 | 1 | 1 | 0.054 | 1.565 | 1.130 | 3.965 | True |
| 1 | 2 | E2 | B1 | 0 | 0 | 0.294 | 1.468 | 0.903 | 4.258 | True |
| 1 | 2 | E3 | B1 | 1 | 1 | 0.369 | 1.545 | 1.219 | 3.947 | True |
| 1 | 2 | E4 | B1 | 1 | 1 | 0.414 | 1.471 | 1.201 | 3.775 | True |
| 1 | 2 | E5 | B1 | 0 | 0 | 0.066 | 1.542 | 0.891 | 4.486 | True |
| 1 | 2 | E6 | B1 | 0 | 0 | 0.345 | 1.339 | 0.801 | 4.386 | True |
| 1 | 3 | E1 | B2 | 1 | 1 | 0.054 | 1.425 | 1.723 | 3.988 | True |
| 1 | 3 | E2 | B2 | 0 | 0 | 0.292 | 2.234 | 1.169 | 4.424 | True |
| 1 | 3 | E3 | B2 | 1 | 1 | 0.336 | 1.727 | 1.412 | 3.912 | True |
| 1 | 3 | E4 | B2 | 1 | 1 | 0.445 | 1.777 | 1.798 | 3.947 | True |
| 1 | 3 | E5 | B2 | 0 | 0 | 0.062 | 1.443 | 1.435 | 4.426 | True |
| 1 | 3 | E6 | B2 | 0 | 0 | 0.259 | 1.441 | 1.526 | 4.298 | True |
| 2 | 1 | E1 | B1 | 1 | 1 | 0.060 | 1.466 | 1.078 | 3.978 | True |
| 2 | 1 | E2 | B1 | 0 | 0 | 0.350 | 2.096 | 0.966 | 4.174 | True |
| 2 | 1 | E3 | B1 | 1 | 1 | 0.389 | 1.472 | 1.124 | 3.953 | True |
| 2 | 1 | E4 | B1 | 1 | 1 | 0.433 | 1.562 | 1.238 | 3.914 | True |
| 2 | 1 | E5 | B1 | 0 | 0 | 0.062 | 1.496 | 0.889 | 4.499 | True |
| 2 | 1 | E6 | B1 | 0 | 0 | 0.301 | 1.526 | 0.987 | 4.314 | True |
| 2 | 2 | E1 | B2 | 1 | 1 | 0.056 | 1.598 | 1.752 | 4.022 | True |
| 2 | 2 | E2 | B2 | 0 | 0 | 0.293 | 1.474 | 1.129 | 4.070 | True |
| 2 | 2 | E3 | B2 | 1 | 1 | 0.293 | 1.503 | 1.490 | 3.860 | True |
| 2 | 2 | E4 | B2 | 1 | 1 | 0.374 | 1.334 | 1.590 | 3.715 | True |
| 2 | 2 | E5 | B2 | 0 | 0 | 0.058 | 1.321 | 1.277 | 4.412 | True |
| 2 | 2 | E6 | B2 | 0 | 0 | 0.245 | 1.267 | 1.351 | 4.132 | True |
| 2 | 3 | E1 | B0 | 3 | 1 | 0.054 | 1.397 | 1.540 | 3.883 | True |
| 2 | 3 | E2 | B0 | 3 | 0 | 0.297 | 1.458 | 1.825 | 4.528 | True |
| 2 | 3 | E3 | B0 | 3 | 1 | 0.644 | 1.507 | 1.497 | 4.918 | True |
| 2 | 3 | E4 | B0 | 3 | 1 | 0.729 | 1.665 | 1.613 | 4.718 | True |
| 2 | 3 | E5 | B0 | 3 | 0 | 0.055 | 1.725 | 1.612 | 6.024 | True |
| 2 | 3 | E6 | B0 | 3 | 0 | 0.236 | 1.908 | 1.633 | 6.879 | True |
| 3 | 1 | E1 | B2 | 1 | 1 | 0.063 | 1.608 | 1.673 | 3.830 | True |
| 3 | 1 | E2 | B2 | 0 | 0 | 0.287 | 1.490 | 1.027 | 4.035 | True |
| 3 | 1 | E3 | B2 | 1 | 1 | 0.315 | 1.358 | 1.357 | 3.832 | True |
| 3 | 1 | E4 | B2 | 1 | 1 | 0.402 | 1.468 | 1.639 | 3.764 | True |
| 3 | 1 | E5 | B2 | 0 | 0 | 0.061 | 1.395 | 1.402 | 4.472 | True |
| 3 | 1 | E6 | B2 | 0 | 0 | 0.249 | 1.349 | 1.333 | 4.178 | True |
| 3 | 2 | E1 | B0 | 3 | 1 | 0.054 | 1.361 | 1.655 | 3.893 | True |
| 3 | 2 | E2 | B0 | 3 | 0 | 0.290 | 1.484 | 1.574 | 4.605 | True |
| 3 | 2 | E3 | B0 | 3 | 1 | 0.605 | 1.481 | 1.494 | 4.837 | True |
| 3 | 2 | E4 | B0 | 3 | 1 | 0.755 | 1.570 | 1.554 | 4.728 | True |
| 3 | 2 | E5 | B0 | 3 | 0 | 0.056 | 1.759 | 1.527 | 5.972 | True |
| 3 | 2 | E6 | B0 | 3 | 0 | 0.242 | 1.890 | 1.541 | 6.948 | True |
| 3 | 3 | E1 | B1 | 1 | 1 | 0.050 | 1.374 | 1.032 | 3.965 | True |
| 3 | 3 | E2 | B1 | 0 | 0 | 0.364 | 1.482 | 0.937 | 4.123 | True |
| 3 | 3 | E3 | B1 | 1 | 1 | 0.289 | 1.357 | 1.110 | 3.830 | True |
| 3 | 3 | E4 | B1 | 1 | 1 | 0.380 | 1.399 | 1.121 | 3.666 | True |
| 3 | 3 | E5 | B1 | 0 | 0 | 0.061 | 1.295 | 0.772 | 4.363 | True |
| 3 | 3 | E6 | B1 | 0 | 0 | 0.245 | 1.261 | 0.863 | 4.144 | True |

B1/B2 matched every measured execution-count reference: True.

The reference enumerates the pre-policy, post-fault cache after execution. Its bound concerns new stages, not time or dollars. Each revision is audited immediately, before subsequent damage or pointer changes. Selected byte snapshots and fault preimages preserve earlier evidence.

Seed/preparation costs are in shared-costs.json and independent clone costs in clone-costs.json. Policy wall, faults and evaluation are measured separately; nested operation durations overlap; do not sum them. Medians are descriptive local measurements, without a stable speed or total-cost claim.

No model policy, hidden evaluation, natural-language interpretation or external utility, process restart, concurrency or remote recovery was evaluated. Source experiment reruns, inference calls, tokens and external API charges were zero. Implementation model costs and local dollar costs were not measured. This trace does not establish an AI advantage or a need for an AI policy.
