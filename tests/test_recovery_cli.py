import subprocess
import sys
from pathlib import Path
from typing import Final

import pytest

ROOT: Final = Path(__file__).parents[1]
SOURCE: Final = ROOT / "runs/phase1-20261010-01/metrics.json"


@pytest.mark.parametrize("run_id", ["../escaped", "nested/run", "", ".", "unsafe value"])
def test_unsafe_cli_run_identity_cannot_create_output(tmp_path: Path, run_id: str) -> None:
    # Given a writable output parent and an unsafe destination identity.
    destination = tmp_path / "output"
    # When the real recovery command parses the identity.
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "src.intent_revalidation.recovery_workflow",
            "--metrics",
            str(SOURCE),
            "--output",
            str(destination),
            "--run-id",
            run_id,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    # Then rejection happens before any study or escaped directory is created.
    assert result.returncode == 2, result.stderr
    assert not tuple(tmp_path.iterdir())


def test_missing_cli_source_does_not_create_run(tmp_path: Path) -> None:
    # Given a missing metrics path and an otherwise safe invocation.
    source = tmp_path / "missing.json"
    destination = tmp_path / "runs"
    # When the CLI loads the original Phase 1 source.
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "src.intent_revalidation.recovery_workflow",
            "--metrics",
            str(source),
            "--output",
            str(destination),
            "--run-id",
            "valid-run",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    # Then the absent source fails before output creation.
    assert result.returncode == 2, result.stderr
    assert not destination.exists()


def test_existing_cli_run_preserves_all_original_files(tmp_path: Path) -> None:
    # Given a prior run whose source and sentinel must never be overwritten.
    destination = tmp_path / "existing"
    destination.mkdir()
    sentinel = destination / "source_metrics.json"
    before = b"preserve this independent earlier result\n"
    _ = sentinel.write_bytes(before)
    # When a caller repeats that output identity through the real CLI.
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "src.intent_revalidation.recovery_workflow",
            "--metrics",
            str(SOURCE),
            "--output",
            str(tmp_path),
            "--run-id",
            destination.name,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    # Then the failed invocation leaves the entire existing directory intact.
    assert result.returncode == 2, result.stderr
    assert tuple(destination.iterdir()) == (sentinel,)
    assert sentinel.read_bytes() == before
