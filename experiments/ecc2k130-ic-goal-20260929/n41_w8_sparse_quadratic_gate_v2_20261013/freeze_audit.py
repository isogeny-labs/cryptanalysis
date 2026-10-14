"""Freeze independent Python audit inputs before execution."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
paths = [HERE / "audit.py", HERE / "result.json", HERE / "run_result.json",
         ROOT / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv",
         ROOT / "n41_basis_aware_quartic_20261011/replay.py",
         ROOT / "n41_w8_quadratic_partial_ideal_v3_20261013/audit_result.json"]
record = {"status": "FROZEN", "cases": [["witness", -1], ["sample", 0]],
          "sources": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
with (HERE / "audit_protocol.json").open("x") as stream:
    json.dump(record, stream, indent=2, sort_keys=True)
    stream.write("\n")
print("FROZEN_SPARSE_QUADRATIC_AUDIT")
