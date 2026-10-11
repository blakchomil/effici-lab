# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
# How to run: python3 tools/verify_report.py <phase>
import hashlib
import json
import pathlib
import re
import sys

root = pathlib.Path(__file__).resolve().parents[1]
phase = sys.argv[1]
if not re.fullmatch(r"[a-z][a-z0-9_-]*", phase):
    raise SystemExit("invalid phase")
report = (root / "out" / (phase + ".json")).read_bytes()
value = json.loads(report)
expected_source = "efe39a97a52d2b073fd80326062ce3a0b8ba63f5c33cfa5504ae706ef02aa36d"
if (type(value) is not dict or value.get("policy_revision") != "gov-v1"
        or value.get("units") != "USD"
        or type(value.get("total")) not in (int, float) or value["total"] != 3
        or value.get("source_sha256") != expected_source
        or hashlib.sha256((root / "input.csv").read_bytes()).hexdigest() != expected_source
        or hashlib.sha256((root / "protected.txt").read_bytes()).hexdigest() != "0d258bfdf65e92dd1b336c622e599b37233ec7fd636e6a1948fbb59cce52a073"):
    raise SystemExit("report or original fixture violates gov-v1")
receipt = {"phase": phase, "policy_revision": "gov-v1",
           "report_sha256": hashlib.sha256(report).hexdigest()}
(root / "receipts" / (phase + ".json")).write_text(json.dumps(receipt) + "\n")
print("verified " + phase)
