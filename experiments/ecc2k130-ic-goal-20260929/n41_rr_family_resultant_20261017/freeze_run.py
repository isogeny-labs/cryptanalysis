"""Bind the monitor to the immutable experiment protocol before execution."""
import hashlib
import json
from pathlib import Path


D = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


p = json.loads((D / "protocol.json").read_text())
record = {"schema": 1, "protocol_sha256": sha(D / "protocol.json"),
          "monitor_sha256": sha(D / "run_monitored.py"),
          "runtime_info_sha256": sha(D / "sage_runtime_info.json")}
assert record["monitor_sha256"] == p["monitor_sha256"]
assert record["runtime_info_sha256"] == p["runtime_info_sha256"]
(D / "run_protocol.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
print(sha(D / "run_protocol.json"))
