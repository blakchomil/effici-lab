# Claude Code pilot: authentication failure, not a governance result

User-facing date: 2026-10-11 KST. Development pilot, excluded from comparison.

The actual Claude Code 2.1.114 process started session
`e056b0bb-ce65-4b30-98d5-6f9ba280e41e` with subscription authentication and
observation-only G0 hooks. A real SessionStart(source=startup) receipt exists.
The first task returned HTTP 401 and `OAuth access token has expired`.
No report task, compaction, restart task or delegation completed. There is no
behavioral result for G0/G1/G2 and no support for a difference between methods.

The early driver then waited for Stop, which the authentication error did not
emit, and timed out. This failure was retained; the driver now detects completed
structured error results promptly. The retained pilot was not rerun or overwritten.
The user clarified that the goal is a useful reusable local tool, rather than
repairing their Tokyo orchestrator. No server connection or credential transfer
was performed.

Evidence: [actual output](continuous.stdout.jsonl), [process receipt](continuous.process.json),
[lifecycle observation](events.jsonl), [fixed fixture](workspace/CLAUDE.md),
[pilot protocol](protocol.md). This pilot did not capture an immutable source
snapshot before execution; current source files should not be treated as its
exact executable revision. The subsequent comparative runner snapshots code
before any model call.

The CLI returned zero token usage and total_cost_usd=0 for the failed request.
This is returned telemetry, not a measurement of subscription cash cost.

This public copy redacts the local home directory. Unmodified originals are retained
privately; [the transformation record](publication-redaction.json) maps file hashes.
