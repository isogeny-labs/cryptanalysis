"""Freeze the N131 W23 first-two-pair resultant transfer control."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCES = {
    "fixture": ROOT / "n131_w23_sixpair_shared_circuit_20261017/fixture.json",
    "public_protocol": ROOT / "n131_w23_sixpair_shared_circuit_20261017/protocol_v3.json",
    "sage_runtime": HERE / "sage_runtime_info.json",
    "producer": HERE / "n131_h_bridge_sage_v2.py",
    "freeze": HERE / "freeze_n131_bridge_v2.py",
    "attempt1_failure": HERE / "n131_bridge_attempt1_failure.json",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


public = json.loads(SOURCES["public_protocol"].read_text())
fixture = json.loads(SOURCES["fixture"].read_text())
assert public["curve_id"] == fixture["curve_id"] == "EC1N131Ckb1heb5f1998f20b"
assert public["public_chart"].startswith("standard reciprocal 1/x")
assert len(public["rotations"]) == 6
record = {"status": "FROZEN_N131_W23_FIRST_TWO_RESULTANT_BRIDGE",
          "candidate_id": None, "curve_id": public["curve_id"],
          "target_kind": "constructed six-pair control",
          "previous_attempt_status": "PRODUCER_FAILURE_TYPE_ERROR",
          "worker_count": 1, "wall_cap_seconds": 120,
          "rss_cap_bytes": 4*1024**3,
          "sources": {name: {"path": str(path), "sha256": sha(path)}
                      for name, path in SOURCES.items()}}
assert not (HERE / "n131_bridge_protocol_v2.json").exists()
(HERE / "n131_bridge_protocol_v2.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
