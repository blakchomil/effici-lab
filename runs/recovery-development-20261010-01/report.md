# Bounded recovery comparison

Independent current-revision audits satisfied: 54/54.

Public synthetic between-revision faults over unchanged actual Phase 1 metrics. Three cyclic policy orders repeat the same six-event trace; these are not independent user incidents or a process-restart study.

| Policy | Satisfied | New stages | Invalid reuse / cache exposures | Median policy wall (ms/event) | Contract checks | Integrity checks | Hashes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B0 | 18/18 | 54 | 0/0 | 1.6209375 | 0 | 0 | 108 |
| B1 | 18/18 | 9 | 0/90 | 1.0177505 | 0 | 60 | 66 |
| B2 | 18/18 | 9 | 0/90 | 1.393333 | 84 | 0 | 174 |

| Repeat | Position | Event | Policy | New stages | Reference | Fault ms | Prep ms | Policy ms | Evaluation ms | Satisfied |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | E1 | B0 | 3 | 1 | 0.068 | 1.054 | 1.701 | 3.977 | True |
| 1 | 1 | E2 | B0 | 3 | 0 | 0.454 | 0.971 | 2.393 | 4.681 | True |
| 1 | 1 | E3 | B0 | 3 | 1 | 0.863 | 1.431 | 1.680 | 5.152 | True |
| 1 | 1 | E4 | B0 | 3 | 1 | 0.976 | 1.284 | 1.786 | 4.858 | True |
| 1 | 1 | E5 | B0 | 3 | 0 | 0.055 | 1.545 | 1.735 | 6.146 | True |
| 1 | 1 | E6 | B0 | 3 | 0 | 0.269 | 1.469 | 1.674 | 7.000 | True |
| 1 | 2 | E1 | B1 | 1 | 1 | 0.059 | 0.887 | 1.047 | 3.839 | True |
| 1 | 2 | E2 | B1 | 0 | 0 | 0.347 | 0.974 | 0.977 | 4.075 | True |
| 1 | 2 | E3 | B1 | 1 | 1 | 0.298 | 0.875 | 1.097 | 3.905 | True |
| 1 | 2 | E4 | B1 | 1 | 1 | 0.401 | 0.994 | 1.158 | 3.764 | True |
| 1 | 2 | E5 | B1 | 0 | 0 | 0.054 | 0.887 | 0.811 | 4.625 | True |
| 1 | 2 | E6 | B1 | 0 | 0 | 0.243 | 0.847 | 0.805 | 4.144 | True |
| 1 | 3 | E1 | B2 | 1 | 1 | 0.051 | 0.891 | 1.530 | 3.944 | True |
| 1 | 3 | E2 | B2 | 0 | 0 | 0.316 | 0.935 | 1.089 | 4.165 | True |
| 1 | 3 | E3 | B2 | 1 | 1 | 0.302 | 0.963 | 1.371 | 3.918 | True |
| 1 | 3 | E4 | B2 | 1 | 1 | 0.378 | 0.974 | 1.603 | 3.924 | True |
| 1 | 3 | E5 | B2 | 0 | 0 | 0.055 | 0.902 | 1.537 | 4.474 | True |
| 1 | 3 | E6 | B2 | 0 | 0 | 0.280 | 0.869 | 1.371 | 4.196 | True |
| 2 | 1 | E1 | B1 | 1 | 1 | 0.052 | 0.929 | 1.228 | 4.033 | True |
| 2 | 1 | E2 | B1 | 0 | 0 | 0.301 | 0.950 | 0.977 | 4.147 | True |
| 2 | 1 | E3 | B1 | 1 | 1 | 0.401 | 1.037 | 1.491 | 4.011 | True |
| 2 | 1 | E4 | B1 | 1 | 1 | 0.471 | 1.017 | 1.235 | 3.816 | True |
| 2 | 1 | E5 | B1 | 0 | 0 | 0.057 | 1.028 | 0.937 | 4.499 | True |
| 2 | 1 | E6 | B1 | 0 | 0 | 0.244 | 0.846 | 0.997 | 4.243 | True |
| 2 | 2 | E1 | B2 | 1 | 1 | 0.051 | 1.014 | 1.719 | 3.957 | True |
| 2 | 2 | E2 | B2 | 0 | 0 | 0.310 | 0.901 | 1.111 | 4.065 | True |
| 2 | 2 | E3 | B2 | 1 | 1 | 0.287 | 0.874 | 1.344 | 3.935 | True |
| 2 | 2 | E4 | B2 | 1 | 1 | 0.360 | 0.931 | 1.769 | 3.711 | True |
| 2 | 2 | E5 | B2 | 0 | 0 | 0.053 | 0.835 | 1.384 | 4.458 | True |
| 2 | 2 | E6 | B2 | 0 | 0 | 0.240 | 0.857 | 1.314 | 4.106 | True |
| 2 | 3 | E1 | B0 | 3 | 1 | 0.058 | 1.048 | 1.633 | 3.945 | True |
| 2 | 3 | E2 | B0 | 3 | 0 | 0.305 | 0.931 | 1.609 | 4.506 | True |
| 2 | 3 | E3 | B0 | 3 | 1 | 0.598 | 0.995 | 1.431 | 4.867 | True |
| 2 | 3 | E4 | B0 | 3 | 1 | 0.726 | 1.124 | 1.573 | 4.716 | True |
| 2 | 3 | E5 | B0 | 3 | 0 | 0.048 | 1.184 | 1.635 | 6.003 | True |
| 2 | 3 | E6 | B0 | 3 | 0 | 0.219 | 1.280 | 1.514 | 7.105 | True |
| 3 | 1 | E1 | B2 | 1 | 1 | 0.050 | 0.963 | 1.538 | 3.856 | True |
| 3 | 1 | E2 | B2 | 0 | 0 | 0.283 | 0.928 | 1.055 | 4.061 | True |
| 3 | 1 | E3 | B2 | 1 | 1 | 0.306 | 0.882 | 1.293 | 3.879 | True |
| 3 | 1 | E4 | B2 | 1 | 1 | 0.353 | 0.920 | 1.561 | 3.723 | True |
| 3 | 1 | E5 | B2 | 0 | 0 | 0.054 | 0.899 | 1.402 | 4.515 | True |
| 3 | 1 | E6 | B2 | 0 | 0 | 0.278 | 0.861 | 1.421 | 4.158 | True |
| 3 | 2 | E1 | B0 | 3 | 1 | 0.049 | 0.926 | 1.470 | 3.943 | True |
| 3 | 2 | E2 | B0 | 3 | 0 | 0.286 | 0.933 | 1.531 | 4.594 | True |
| 3 | 2 | E3 | B0 | 3 | 1 | 0.577 | 1.004 | 1.491 | 4.852 | True |
| 3 | 2 | E4 | B0 | 3 | 1 | 0.725 | 1.027 | 1.548 | 4.651 | True |
| 3 | 2 | E5 | B0 | 3 | 0 | 0.048 | 1.244 | 1.518 | 5.966 | True |
| 3 | 2 | E6 | B0 | 3 | 0 | 0.255 | 1.370 | 1.646 | 6.978 | True |
| 3 | 3 | E1 | B1 | 1 | 1 | 0.055 | 0.882 | 1.065 | 3.848 | True |
| 3 | 3 | E2 | B1 | 0 | 0 | 0.343 | 1.085 | 0.918 | 4.131 | True |
| 3 | 3 | E3 | B1 | 1 | 1 | 0.283 | 0.850 | 1.089 | 3.837 | True |
| 3 | 3 | E4 | B1 | 1 | 1 | 0.357 | 0.955 | 1.039 | 3.740 | True |
| 3 | 3 | E5 | B1 | 0 | 0 | 0.051 | 0.912 | 0.757 | 4.333 | True |
| 3 | 3 | E6 | B1 | 0 | 0 | 0.233 | 0.873 | 0.757 | 4.236 | True |

B1/B2 matched every measured execution-count reference: True.

The reference enumerates the pre-policy, post-fault cache after policy completion. Its bound concerns new stages, not time or dollars. Each revision is audited immediately, before subsequent damage or pointer changes. Selected byte snapshots and fault preimages preserve earlier evidence.

Seed/preparation costs are in shared-costs.json and independent clone costs in clone-costs.json. Policy wall, fault injection and evaluator overhead are separate; nested operation durations overlap and must not be summed. Medians are descriptive local measurements, without a stable speed or total-cost claim.

No model policy, hidden evaluation, natural-language interpretation, external user utility, process restart, concurrency or remote recovery was evaluated. Source experiment reruns, inference calls, tokens and external API charges were zero. Implementation model costs and local dollar costs were not measured. This trace does not establish an AI advantage or a need for an AI policy.
