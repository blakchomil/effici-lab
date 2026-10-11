# Governance Guard

A local, dependency-free tool for keeping configured instructions visible and
requiring a fresh successful check before explicitly configured Claude Bash commands.
It does not need Claude authentication for its own commands.

From this research repository, initialize a separate project:

```sh
python3 -m src.intent_revalidation.governance_guard init \
  --root /absolute/path/to/project \
  --instructions CLAUDE.md \
  --track 'src/**/*.py' --track 'tests/**/*.py' --track 'verify.py' \
  --check 'python3 verify.py' \
  --gate 'python3 publish.py' --protect protected.txt
python3 -m src.intent_revalidation.governance_guard context --root /absolute/path/to/project
python3 -m src.intent_revalidation.governance_guard check --root /absolute/path/to/project
python3 -m src.intent_revalidation.governance_guard status --root /absolute/path/to/project
```

Use `--instructions AGENTS.md` explicitly when that is the project's source of
instructions. Repeat the option to include multiple sources. Configure `--track`
to include every file affecting the check, including the verifier itself. Patterns
are Python `Path.glob` patterns. Instructions and the effective policy are always
hashed. No tracked files means only the instructions and policy are fingerprinted.

Initialization creates `.governance/policy.json` and prints the generated settings
path and JSON. It refuses to overwrite an existing policy. It does not modify
Claude's project or global settings. To opt into these hooks for one Claude session,
start Claude from the project with:

```sh
claude --settings /absolute/path/to/project/.governance/session-settings.json
```

The generated command references the current Python interpreter and this repository;
keep both paths available. SessionStart (including compact/resume) and SubagentStart
inject current instruction text and hashes. PreToolUse examines Bash/Write/Edit.
An exact configured argv prefix requires a matching successful receipt. Recognizable
gated commands embedded in shell expressions are rejected rather than interpreted.
Write/Edit of `.governance` or configured protected files is rejected. Other tools
and commands remain outside this bounded gate.

Each check runs the human-configured argv with `shell=False` in the target project,
with a timeout (default 60 seconds, `check --timeout SECONDS`). Receipts are created
exclusively under `.governance/receipts/<uuid>.json` and retain stdout, stderr,
exit status and before/after fingerprints. Changed tracked bytes, added/deleted files,
instructions or policy invalidate a receipt. A check that changes its own tracked
inputs cannot produce a passing receipt.

## Boundaries

This is an opt-in workflow helper, not a security sandbox. A process with filesystem
access can edit policy or fabricate receipts; exclusive writes prevent accidental
overwriting, not malicious tampering. Bash can modify protected paths; wrappers,
aliases, scripts and alternate tools can bypass the deliberately limited command
matching. Hashes do not establish instruction comprehension or semantic correctness.
A successful check means only that the configured check succeeded on those bytes.
External state, untracked files, dependency/environment changes, and changes between
the gate decision and command execution are not covered. Do not configure a check
that spawns detached children. Shell compound detection intentionally can reject
harmless commands containing a gate executable; invoke gated commands directly.

The CLI and hook protocol can be tested locally without any model. Such runs are
tool verification, not evidence that an AI obeys instructions after compression,
restart or delegation; those claims require an actual agent lifecycle experiment.
