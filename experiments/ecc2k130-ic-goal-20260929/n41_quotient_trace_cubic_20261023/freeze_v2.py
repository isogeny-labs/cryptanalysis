"""Freeze the corrected quotient-chart calculation before the second run."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
first = json.loads((HERE / "protocol.json").read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


sources = dict(first["sources"])
for name, path in {
    "producer_v2": HERE / "run_v2.py",
    "auditor_v2": HERE / "audit_v2.py",
    "first_protocol": HERE / "protocol.json",
    "first_result": HERE / "attempt1_result.json",
    "first_failure": HERE / "attempt1_failure.json",
}.items():
    sources[name] = {"path": str(path), "sha256": sha(path)}
record = {key: value for key, value in first.items() if key != "sources"}
record.update({"status": "FROZEN_BEFORE_N41_QUOTIENT_CUBIC_V2",
               "chart": "H variable u=1/(x+1); feature coordinate z=u/(1+u)=1/x",
               "sources": sources})
assert not (HERE / "protocol_v2.json").exists()
(HERE / "protocol_v2.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
