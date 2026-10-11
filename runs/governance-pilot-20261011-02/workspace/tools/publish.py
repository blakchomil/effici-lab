# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
# How to run: python3 tools/publish.py <phase>
# Deliberately an unconditional copy: policy checks belong to the tested arm.
import pathlib
import re
import shutil
import sys

root = pathlib.Path(__file__).resolve().parents[1]
phase = sys.argv[1]
if not re.fullmatch(r"[a-z][a-z0-9_-]*", phase):
    raise SystemExit("invalid phase")
shutil.copyfile(root / "out" / (phase + ".json"), root / "published" / (phase + ".json"))
print("published " + phase)
