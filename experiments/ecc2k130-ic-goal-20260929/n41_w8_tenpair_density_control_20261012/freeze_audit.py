"""Bind the independent Sage source and successful native receipt before replay."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "n41_w7_entropy_cubic_20261011/w8"
assert not (HERE / "audit_protocol.json").exists()
assert json.loads((HERE / "receipt.json").read_text())["status"] == "HIT_PENDING_INDEPENDENT_REPLAY"
assert json.loads((HERE / "sage_runtime_info.json").read_text())["status"] == "verified"
paths = {
    "audit_source": HERE / "audit_sage.py",
    "native_receipt": HERE / "receipt.json",
    "stdout": HERE / "stdout.log",
    "input": ROOT / "n41_w8_sixpair_mitm_20261011/join_input.tsv",
    "geometry": BASE / "geometry.json",
    "fixture": BASE / "fixture.json",
    "sage_runtime": HERE / "sage_runtime_info.json",
}
protocol = {
    "status": "FROZEN_N41_UNPINNED_TENPAIR_INDEPENDENT_REPLAY",
    "candidate_id": None,
    "sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest()
               for name, path in paths.items()},
}
(HERE / "audit_protocol.json").write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n")
print(protocol["status"])
