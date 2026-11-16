"""Verify sealed bucket-mass proof and exhaustive finite control."""
import gzip
import hashlib
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parent
entries = (root / "SEAL.sha256").read_text().splitlines()
for entry in entries:
    digest, name = entry.split("  ", 1)
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
protocol = json.loads((root / "protocol.json").read_text())
result = json.loads((root / "result.json").read_text())
assert protocol["schema"] == "xedni-bucket-fiber-partition-protocol-v1"
assert result["schema"] == "xedni-bucket-fiber-partition-result-v1"
assert result["status"] == "PASS" and result["mismatches"] == 0
assert result["executions"] == 35280
assert result["cells_checked"] == 137200
assert result["positive_fiber_cells"] == 8617
assert result["zero_fiber_cells"] == 128583
for k, row in result["by_length"].items():
    assert k in ("2", "3", "4", "5")
    assert row["fiber"] == 35280
    assert row["first_hit"] <= row["live"] <= 35280
raw = root / "positive-bucket-rows.jsonl.gz"
assert hashlib.sha256(raw.read_bytes()).hexdigest() == result["rows_sha256"]
with gzip.open(raw, "rt") as rows:
    assert sum(1 for _ in rows) == 8617
source = (root / "formal/BucketFiberPartition.lean").read_text()
build = (root / "formal/build-output.txt").read_text()
assert "Build completed successfully (3151 jobs)." in build
for bad in ("sorry", "admit", "sorryAx", "native_decide", "axiom "):
    assert bad not in source
assert "sorryAx" not in build and "error:" not in build
names = re.findall(r"^#print axioms (\w+)$", source, re.M)
assert len(names) == 14
for name in names:
    prefix = re.escape("'XedniBucketFiberPartition." + name + "'")
    matches = re.findall(prefix + r" depends on axioms: \[([^\]]+)\]", build, re.S)
    if matches:
        assert len(matches) == 1, name
        assert {a.strip() for a in matches[0].split(",")} <= {
            "propext", "Classical.choice", "Quot.sound"}, name
    else:
        assert len(re.findall(prefix + r" does not depend on any axioms", build)) == 1, name
print(json.dumps({"status": "PASS", "sealed_files": len(entries),
                  "lean_declarations": len(names), "cells": 137200}, sort_keys=True))
