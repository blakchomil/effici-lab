"""Execute the configured verifier and keep append-only receipt files."""

from __future__ import annotations

import subprocess
from json import JSONDecodeError
from uuid import uuid4

from src.intent_revalidation.fixtures import mapping
from src.intent_revalidation.model import InputError, JsonObject, canonical, decode_json

from .policy import Policy, confined, load, snapshot


def check(policy: Policy, timeout: float = 60) -> JsonObject:
    """Execute only policy argv without a shell and capture before/after state."""
    if timeout <= 0:
        raise InputError("timeout", "must be positive")
    before = snapshot(policy)
    exit_code = -1
    stdout = ""
    stderr = ""
    after: JsonObject
    try:
        result = subprocess.run(  # noqa: S603 -- human configured argv, no shell
            policy.command,
            cwd=policy.root,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        exit_code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except (OSError, subprocess.TimeoutExpired) as error:
        stderr = str(error)
    try:
        after = snapshot(load(policy.root))
    except (OSError, InputError, JSONDecodeError) as error:
        after = {"error": str(error)}
    receipt: JsonObject = {
        "id": uuid4().hex,
        "before": before,
        "after": after,
        "argv": list(policy.command),
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "passed": exit_code == 0 and before == after,
    }
    folder = confined(policy.root, ".governance/receipts")
    folder.mkdir(parents=True, exist_ok=True)
    path = confined(policy.root, f".governance/receipts/{receipt['id']}.json")
    with path.open("x") as handle:
        _ = handle.write(canonical(receipt).decode() + "\n")
    return receipt


def status(policy: Policy) -> JsonObject:
    """Accept only a recorded success matching current policy and source bytes."""
    current = snapshot(policy)
    folder = confined(policy.root, ".governance/receipts")
    for path in sorted(
        folder.glob("*.json"), key=lambda item: item.stat().st_mtime_ns, reverse=True
    ):
        try:
            safe_path = confined(policy.root, path.relative_to(policy.root).as_posix())
            receipt = mapping(decode_json(safe_path.read_text()))
        except (OSError, InputError, JSONDecodeError):
            continue
        if receipt.get("before") == current:
            valid = (
                receipt.get("passed") is True
                and receipt.get("exit_code") == 0
                and receipt.get("argv") == list(policy.command)
                and receipt.get("after") == current
            )
            return {"valid": valid, "receipt": path.name, "snapshot": current}
    return {"valid": False, "receipt": None, "snapshot": current}
