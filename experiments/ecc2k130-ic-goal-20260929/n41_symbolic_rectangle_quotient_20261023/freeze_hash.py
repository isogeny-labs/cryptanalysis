"""Freeze deterministic target-bit equality products before the region run."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
prior = json.loads((HERE / "protocol_v2.json").read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


sources = dict(prior["sources"])
for name, path in {
    "producer_hash": HERE / "run_hash.py",
    "auditor_hash": HERE / "audit_hash_sage.py",
    "freeze_hash": HERE / "freeze_hash.py",
    "adaptive_result": HERE / "adaptive_result.json",
    "adaptive_audit": HERE / "adaptive_audit_result.json",
}.items():
    sources[name] = {"path": str(path), "sha256": sha(path)}
record = {key: value for key, value in prior.items()
          if key not in ("sources", "selection", "status")}
record.update({"status": "FROZEN_N41_QUOTIENT_FINGERPRINT",
               "selection": "Use the first 24 representation bits of z=1/x in increasing order for all 132 complete 2x2 rectangles; zero indicator stops a rectangle early.",
               "checkpoints": [8, 12, 16, 24],
               "sources": sources})
assert len(record["rectangles"]) == 132
assert not (HERE / "hash_protocol.json").exists()
(HERE / "hash_protocol.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
