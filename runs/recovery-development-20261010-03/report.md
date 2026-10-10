# Bounded recovery comparison

Independent current-revision audits satisfied: 54/54.

Public synthetic between-revision faults over unchanged actual Phase 1 metrics. Three cyclic policy orders repeat the same six-event trace; these are not independent user incidents or a process-restart study.

| Policy | Satisfied | New stages | Invalid reuse / cache exposures | Median policy wall (ms/event) | Contract checks | Integrity checks | Hashes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B0 | 18/18 | 54 | 0/0 | 1.6115415 | 0 | 0 | 108 |
| B1 | 18/18 | 9 | 0/90 | 1.0334795 | 0 | 60 | 66 |
| B2 | 18/18 | 9 | 0/90 | 1.3937915 | 84 | 0 | 174 |

| Repeat | Position | Event | Policy | New stages | Reference | Fault ms | Prep ms | Policy ms | Evaluation ms | Satisfied |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | E1 | B0 | 3 | 1 | 0.067 | 1.471 | 1.652 | 4.035 | True |
| 1 | 1 | E2 | B0 | 3 | 0 | 0.337 | 1.621 | 1.941 | 4.748 | True |
| 1 | 1 | E3 | B0 | 3 | 1 | 0.649 | 1.617 | 1.565 | 5.042 | True |
| 1 | 1 | E4 | B0 | 3 | 1 | 0.877 | 1.751 | 1.794 | 4.828 | True |
| 1 | 1 | E5 | B0 | 3 | 0 | 0.064 | 1.810 | 1.598 | 6.013 | True |
| 1 | 1 | E6 | B0 | 3 | 0 | 0.281 | 2.116 | 1.628 | 7.123 | True |
| 1 | 2 | E1 | B1 | 1 | 1 | 0.054 | 1.476 | 1.186 | 4.045 | True |
| 1 | 2 | E2 | B1 | 0 | 0 | 0.316 | 1.601 | 0.857 | 4.092 | True |
| 1 | 2 | E3 | B1 | 1 | 1 | 0.353 | 1.577 | 1.296 | 4.072 | True |
| 1 | 2 | E4 | B1 | 1 | 1 | 0.453 | 1.522 | 1.277 | 3.907 | True |
| 1 | 2 | E5 | B1 | 0 | 0 | 0.053 | 1.353 | 0.816 | 4.483 | True |
| 1 | 2 | E6 | B1 | 0 | 0 | 0.261 | 1.502 | 0.887 | 4.333 | True |
| 1 | 3 | E1 | B2 | 1 | 1 | 0.064 | 1.585 | 1.800 | 3.892 | True |
| 1 | 3 | E2 | B2 | 0 | 0 | 0.369 | 1.713 | 1.246 | 4.207 | True |
| 1 | 3 | E3 | B2 | 1 | 1 | 0.318 | 1.432 | 1.563 | 4.062 | True |
| 1 | 3 | E4 | B2 | 1 | 1 | 0.366 | 1.456 | 1.557 | 3.808 | True |
| 1 | 3 | E5 | B2 | 0 | 0 | 0.065 | 1.312 | 1.292 | 4.373 | True |
| 1 | 3 | E6 | B2 | 0 | 0 | 0.236 | 1.402 | 1.502 | 4.281 | True |
| 2 | 1 | E1 | B1 | 1 | 1 | 0.066 | 1.545 | 1.226 | 3.970 | True |
| 2 | 1 | E2 | B1 | 0 | 0 | 0.296 | 1.539 | 0.909 | 4.197 | True |
| 2 | 1 | E3 | B1 | 1 | 1 | 0.363 | 1.526 | 1.223 | 4.164 | True |
| 2 | 1 | E4 | B1 | 1 | 1 | 0.418 | 2.274 | 1.166 | 3.878 | True |
| 2 | 1 | E5 | B1 | 0 | 0 | 0.067 | 1.554 | 0.877 | 4.636 | True |
| 2 | 1 | E6 | B1 | 0 | 0 | 0.247 | 1.479 | 0.954 | 4.413 | True |
| 2 | 2 | E1 | B2 | 1 | 1 | 0.053 | 1.482 | 1.705 | 4.087 | True |
| 2 | 2 | E2 | B2 | 0 | 0 | 0.361 | 1.532 | 1.165 | 4.171 | True |
| 2 | 2 | E3 | B2 | 1 | 1 | 0.309 | 1.417 | 1.371 | 3.980 | True |
| 2 | 2 | E4 | B2 | 1 | 1 | 0.406 | 1.500 | 1.607 | 3.764 | True |
| 2 | 2 | E5 | B2 | 0 | 0 | 0.058 | 1.343 | 1.317 | 4.414 | True |
| 2 | 2 | E6 | B2 | 0 | 0 | 0.253 | 1.352 | 1.375 | 4.216 | True |
| 2 | 3 | E1 | B0 | 3 | 1 | 0.053 | 1.426 | 1.535 | 3.897 | True |
| 2 | 3 | E2 | B0 | 3 | 0 | 0.313 | 1.454 | 1.615 | 4.634 | True |
| 2 | 3 | E3 | B0 | 3 | 1 | 0.627 | 1.650 | 1.593 | 4.989 | True |
| 2 | 3 | E4 | B0 | 3 | 1 | 0.780 | 1.762 | 1.825 | 4.832 | True |
| 2 | 3 | E5 | B0 | 3 | 0 | 0.052 | 1.772 | 1.615 | 6.043 | True |
| 2 | 3 | E6 | B0 | 3 | 0 | 0.231 | 1.916 | 1.608 | 7.020 | True |
| 3 | 1 | E1 | B2 | 1 | 1 | 0.059 | 1.505 | 1.748 | 4.015 | True |
| 3 | 1 | E2 | B2 | 0 | 0 | 0.284 | 1.488 | 1.008 | 4.150 | True |
| 3 | 1 | E3 | B2 | 1 | 1 | 0.340 | 1.467 | 1.413 | 3.902 | True |
| 3 | 1 | E4 | B2 | 1 | 1 | 0.388 | 1.485 | 1.671 | 3.774 | True |
| 3 | 1 | E5 | B2 | 0 | 0 | 0.063 | 1.364 | 1.319 | 4.436 | True |
| 3 | 1 | E6 | B2 | 0 | 0 | 0.254 | 1.433 | 1.365 | 4.249 | True |
| 3 | 2 | E1 | B0 | 3 | 1 | 0.054 | 1.464 | 1.518 | 3.964 | True |
| 3 | 2 | E2 | B0 | 3 | 0 | 0.285 | 1.468 | 1.651 | 4.713 | True |
| 3 | 2 | E3 | B0 | 3 | 1 | 0.648 | 1.507 | 1.474 | 4.940 | True |
| 3 | 2 | E4 | B0 | 3 | 1 | 0.804 | 1.538 | 1.532 | 4.749 | True |
| 3 | 2 | E5 | B0 | 3 | 0 | 0.052 | 1.708 | 1.556 | 6.062 | True |
| 3 | 2 | E6 | B0 | 3 | 0 | 0.261 | 2.246 | 1.637 | 6.929 | True |
| 3 | 3 | E1 | B1 | 1 | 1 | 0.050 | 1.456 | 1.113 | 3.955 | True |
| 3 | 3 | E2 | B1 | 0 | 0 | 0.341 | 1.504 | 0.825 | 4.279 | True |
| 3 | 3 | E3 | B1 | 1 | 1 | 0.297 | 1.358 | 1.115 | 3.925 | True |
| 3 | 3 | E4 | B1 | 1 | 1 | 0.370 | 1.404 | 1.186 | 3.748 | True |
| 3 | 3 | E5 | B1 | 0 | 0 | 0.060 | 1.391 | 0.824 | 4.586 | True |
| 3 | 3 | E6 | B1 | 0 | 0 | 0.253 | 1.293 | 0.866 | 4.171 | True |

B1/B2 matched every measured execution-count reference: True.

The reference enumerates the pre-policy, post-fault cache after execution. Its bound concerns new stages, not time or dollars. Each revision is audited immediately, before subsequent damage or pointer changes. Selected byte snapshots and fault preimages preserve earlier evidence.

Seed/preparation costs are in shared-costs.json and independent clone costs in clone-costs.json. Policy wall, faults and evaluation are measured separately; nested operation durations overlap; do not sum them. Medians are descriptive local measurements, without a stable speed or total-cost claim.

No model policy, hidden evaluation, natural-language interpretation or external utility, process restart, concurrency or remote recovery was evaluated. Source experiment reruns, inference calls, tokens and external API charges were zero. Human time, implementation model costs and local dollar costs were unmeasured. This trace does not establish an AI advantage or a need for an AI policy.
