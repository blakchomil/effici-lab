# Between-revision report recovery protocol

Fixed before measured execution, 2026-10-10 KST.

## Question and scope

Can the existing deterministic report policies recover from unavailable or damaged cache
bytes during sequential changes without consuming invalid results or regenerating every stage?

This is one public development trace with deliberately injected local faults. It is not an
observed user incident, a natural-language benchmark, a process-restart experiment, or an
external reproduction. The preserved Phase 1 metrics and their numeric values remain unchanged.
No additional paid API calls or evaluated model policies are used.

## Hypothesis and counterexample

B1's granular keys, full-history search and integrity checks, and B2's executable contracts
may recover by selecting an older valid artifact or regenerating only an unavailable role.
Full recomputation B0 is the correctness reference. More selective stage counts need not
mean less work: B2 recomputes expected content during checks and may cost more than B0 here.

The hypothesis fails for this trace if an arm consumes or publishes invalid cached content,
does not satisfy the current report contract, or cannot complete after these between-revision
faults. Extra executions over the independent post-fault bound count against efficiency.
An audit that misses a stale publication after restoration is also a verification failure.

## Shared seed and policy streams

Use `runs/phase1-20261010-01/metrics.json` as immutable source evidence. Create two actual
B0 initial revisions over all five cases, default columns and title `Phase 1 results`.
The measured seed therefore contains six executed stages and two historical candidates for
each role. Clone this same seed into independent B0/B1/B2 streams. Each stream then retains
its own genuinely produced history; do not inject another policy's later outputs into it.

Run three repetitions, with cyclic policy orders B0/B1/B2, B1/B2/B0 and B2/B0/B1.
Repetitions are measurements of the same trace, not independent requests or incidents.
Policies retain their existing implementation, information, tools and execution permissions.

## Trace

| Event | Current requirement or fault before selection | Selective execution-count hypothesis |
| --- | --- | ---: |
| E1 | Change title to `Recovery comparison`; preserve numbers and columns | 1 |
| E2 | Keep E1 requirements; delete newest eligible SUMMARY bytes, with older history available | 0 |
| E3 | Keep E1 requirements; delete all currently eligible SUMMARY bytes | 1 |
| E4 | Keep E1 requirements; corrupt all eligible RENDER bytes without changing recorded digests or keys | 1 |
| E5 | Return to the original title and columns | 0 |
| E6 | Keep original requirements; delete newest eligible SELECT bytes, with older history available | 0 |

Eligibility uses the existing role-specific key and current predecessor content. The same
fault rule applies to every policy; actual candidate IDs and counts may differ after their
own prior work. Never select fault targets using independent evaluator answers. Missing
files are not deleted a second time. Archive original bytes and record artifact identity,
generation revision, action and before/after hashes before modifying clone-local files.
The shared seed and earlier published experiment folders are never damaged or rewritten.

## Independent checks and accounting

For each event, record its cache state after injection and before policy selection. Only
after execution, enumerate that recorded cache's feasible plans with the independent source
oracle, and audit all actual binding, consumption and publication events immediately.
Save each audit before the next fault changes bytes or the publication pointer. Do not
reinterpret a historical audit as a current check of subsequently damaged files.

The oracle reconstructs stage content and visible report numbers from the original source
bytes. Reference costs are unit counts of new stages, not time or dollar optima. Expected
selective counts above are hypotheses, not values supplied to policy selection.

Measure input preparation, seed generation, clone, fault injection, policy wall time,
execution/check/hash/reuse operations, and separate evaluation/reference time. Nested
operation durations overlap and must not be summed. Report all repetitions and descriptive
timing summaries; small local timings do not establish stable general savings. Human time,
development-model usage, local dollar cost and external usefulness remain unmeasured.

Separately verify that a stale publication followed by restoring the correct output still
fails the event-history audit. This negative control is excluded from successful policy-arm
totals and its work is recorded separately from the comparison.

## Stop and next decision

Finish after the actual CLI trace, independent negative control, meaningful regressions,
strict checks and recorded results. If B1/B2 meet correctness and the stage-count bound,
conclude only that the existing deterministic methods suffice for these local faults.
Do not infer AI superiority, durable restart recovery, concurrency safety or a reduction
in human revision effort. The external-person reproduction task remains outstanding.
