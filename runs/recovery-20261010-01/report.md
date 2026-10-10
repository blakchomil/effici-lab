# Bounded recovery comparison

Independent current-revision audits satisfied: 54/54.

Public synthetic between-revision faults over unchanged actual Phase 1 metrics. Three cyclic policy orders repeat the same six-event trace; these are not independent user incidents or a process-restart study.

| Policy | Satisfied | New stages | Invalid reuse / cache exposures | Median policy wall (ms/event) | Contract checks | Integrity checks | Hashes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B0 | 18/18 | 54 | 0/0 | 1.544833 | 0 | 0 | 108 |
| B1 | 18/18 | 9 | 0/90 | 1.0310205 | 0 | 60 | 66 |
| B2 | 18/18 | 9 | 0/90 | 1.3604995 | 84 | 0 | 174 |

| Repeat | Position | Event | Policy | New stages | Reference | Fault ms | Prep ms | Policy ms | Evaluation ms | Satisfied |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | E1 | B0 | 3 | 1 | 0.053 | 1.442 | 1.579 | 3.970 | True |
| 1 | 1 | E2 | B0 | 3 | 0 | 0.328 | 1.477 | 1.600 | 4.630 | True |
| 1 | 1 | E3 | B0 | 3 | 1 | 0.631 | 1.804 | 1.540 | 4.881 | True |
| 1 | 1 | E4 | B0 | 3 | 1 | 0.731 | 1.678 | 1.587 | 4.652 | True |
| 1 | 1 | E5 | B0 | 3 | 0 | 0.054 | 1.592 | 1.450 | 5.985 | True |
| 1 | 1 | E6 | B0 | 3 | 0 | 0.228 | 1.731 | 1.447 | 6.800 | True |
| 1 | 2 | E1 | B1 | 1 | 1 | 0.053 | 1.381 | 1.053 | 3.871 | True |
| 1 | 2 | E2 | B1 | 0 | 0 | 0.301 | 1.564 | 0.784 | 4.296 | True |
| 1 | 2 | E3 | B1 | 1 | 1 | 0.336 | 1.517 | 1.181 | 4.053 | True |
| 1 | 2 | E4 | B1 | 1 | 1 | 0.451 | 1.618 | 1.206 | 3.833 | True |
| 1 | 2 | E5 | B1 | 0 | 0 | 0.057 | 1.412 | 0.827 | 4.637 | True |
| 1 | 2 | E6 | B1 | 0 | 0 | 0.267 | 1.813 | 1.513 | 4.279 | True |
| 1 | 3 | E1 | B2 | 1 | 1 | 0.076 | 1.477 | 1.895 | 3.926 | True |
| 1 | 3 | E2 | B2 | 0 | 0 | 0.301 | 1.418 | 1.151 | 4.124 | True |
| 1 | 3 | E3 | B2 | 1 | 1 | 0.285 | 1.396 | 1.382 | 4.020 | True |
| 1 | 3 | E4 | B2 | 1 | 1 | 0.351 | 1.424 | 1.716 | 3.729 | True |
| 1 | 3 | E5 | B2 | 0 | 0 | 0.051 | 1.384 | 1.399 | 4.375 | True |
| 1 | 3 | E6 | B2 | 0 | 0 | 0.225 | 1.229 | 1.321 | 4.110 | True |
| 2 | 1 | E1 | B1 | 1 | 1 | 0.058 | 1.366 | 1.040 | 3.854 | True |
| 2 | 1 | E2 | B1 | 0 | 0 | 0.280 | 1.438 | 0.788 | 4.052 | True |
| 2 | 1 | E3 | B1 | 1 | 1 | 0.308 | 1.261 | 1.112 | 3.781 | True |
| 2 | 1 | E4 | B1 | 1 | 1 | 0.366 | 1.356 | 1.072 | 3.737 | True |
| 2 | 1 | E5 | B1 | 0 | 0 | 0.055 | 1.255 | 0.771 | 4.323 | True |
| 2 | 1 | E6 | B1 | 0 | 0 | 0.235 | 1.311 | 0.797 | 4.241 | True |
| 2 | 2 | E1 | B2 | 1 | 1 | 0.053 | 1.411 | 1.518 | 3.796 | True |
| 2 | 2 | E2 | B2 | 0 | 0 | 0.283 | 1.333 | 1.055 | 4.006 | True |
| 2 | 2 | E3 | B2 | 1 | 1 | 0.285 | 1.347 | 1.339 | 3.796 | True |
| 2 | 2 | E4 | B2 | 1 | 1 | 0.413 | 1.379 | 1.699 | 3.684 | True |
| 2 | 2 | E5 | B2 | 0 | 0 | 0.055 | 1.415 | 1.423 | 4.275 | True |
| 2 | 2 | E6 | B2 | 0 | 0 | 0.231 | 1.272 | 1.290 | 4.069 | True |
| 2 | 3 | E1 | B0 | 3 | 1 | 0.050 | 1.324 | 1.459 | 3.817 | True |
| 2 | 3 | E2 | B0 | 3 | 0 | 0.296 | 1.424 | 1.618 | 4.480 | True |
| 2 | 3 | E3 | B0 | 3 | 1 | 0.583 | 1.615 | 1.574 | 4.791 | True |
| 2 | 3 | E4 | B0 | 3 | 1 | 0.738 | 1.707 | 1.617 | 4.752 | True |
| 2 | 3 | E5 | B0 | 3 | 0 | 0.055 | 1.732 | 1.575 | 5.903 | True |
| 2 | 3 | E6 | B0 | 3 | 0 | 0.240 | 1.739 | 1.575 | 6.825 | True |
| 3 | 1 | E1 | B2 | 1 | 1 | 0.065 | 1.344 | 1.518 | 3.805 | True |
| 3 | 1 | E2 | B2 | 0 | 0 | 0.305 | 1.400 | 1.224 | 4.102 | True |
| 3 | 1 | E3 | B2 | 1 | 1 | 0.295 | 1.414 | 1.265 | 3.830 | True |
| 3 | 1 | E4 | B2 | 1 | 1 | 0.358 | 1.356 | 1.532 | 3.722 | True |
| 3 | 1 | E5 | B2 | 0 | 0 | 0.050 | 1.370 | 1.299 | 4.409 | True |
| 3 | 1 | E6 | B2 | 0 | 0 | 0.250 | 1.289 | 1.328 | 4.070 | True |
| 3 | 2 | E1 | B0 | 3 | 1 | 0.052 | 1.378 | 1.549 | 3.836 | True |
| 3 | 2 | E2 | B0 | 3 | 0 | 0.279 | 1.338 | 1.532 | 4.538 | True |
| 3 | 2 | E3 | B0 | 3 | 1 | 0.579 | 1.479 | 1.474 | 4.793 | True |
| 3 | 2 | E4 | B0 | 3 | 1 | 0.806 | 1.508 | 1.432 | 4.705 | True |
| 3 | 2 | E5 | B0 | 3 | 0 | 0.051 | 1.639 | 1.456 | 5.892 | True |
| 3 | 2 | E6 | B0 | 3 | 0 | 0.233 | 1.823 | 1.511 | 6.912 | True |
| 3 | 3 | E1 | B1 | 1 | 1 | 0.054 | 1.367 | 1.022 | 3.784 | True |
| 3 | 3 | E2 | B1 | 0 | 0 | 0.306 | 1.372 | 0.817 | 4.015 | True |
| 3 | 3 | E3 | B1 | 1 | 1 | 0.289 | 1.310 | 1.280 | 3.923 | True |
| 3 | 3 | E4 | B1 | 1 | 1 | 0.355 | 1.344 | 1.208 | 3.685 | True |
| 3 | 3 | E5 | B1 | 0 | 0 | 0.053 | 1.296 | 0.734 | 4.334 | True |
| 3 | 3 | E6 | B1 | 0 | 0 | 0.257 | 1.353 | 0.873 | 4.123 | True |

B1/B2 matched every measured execution-count reference: True.

The reference enumerates the pre-policy, post-fault cache after execution. Its bound concerns new stages, not time or dollars. Each revision is audited immediately, before subsequent damage or pointer changes. Selected byte snapshots and fault preimages preserve earlier evidence.

Seed/preparation costs are in shared-costs.json and independent clone costs in clone-costs.json. Policy wall, faults and evaluation are measured separately; nested operation durations overlap; do not sum them. Medians are descriptive local measurements, without a stable speed or total-cost claim.

No model policy, hidden evaluation, natural-language interpretation or external utility, process restart, concurrency or remote recovery was evaluated. Source experiment reruns, inference calls, tokens and external API charges were zero. Human time, implementation model costs and local dollar costs were unmeasured. This trace does not establish an AI advantage or a need for an AI policy.
