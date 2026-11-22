"""Freeze the corrected N131 direct-child resource supervisor."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
protocol = HERE / "protocol_n131_v3.json"
assert not protocol.exists()
prior = json.loads((HERE / "n41_supervisor.json").read_text())
assert prior["status"] == "PASS_N41_BLOCK_NORM_GATE"
attempt = json.loads((HERE / "attempt2/attempt.json").read_text())
assert attempt["status"] == "PARENT_MONITOR_FAILURE_CHILD_COMPLETED"
sources = {"worker_protocol": HERE / "protocol_n131.json",
           "worker_script": HERE / "blocknorm_sage.py",
           "supervisor": HERE / "supervise_v3.py",
           "freeze_script": Path(__file__),
           "n41_supervisor": HERE / "n41_supervisor.json",
           "attempt2": HERE / "attempt2/attempt.json",
           "runtime": HERE / "sage_runtime_info.json"}
cfg = {"status": "FROZEN_BEFORE_N131_BLOCK_NORM_V3",
       "case": "n131", "candidate_id": None,
       "curve_id": "EC1N131Ckb1heb5f1998f20b",
       "sage_launcher": "/Volumes/SSD990/cryptanalysis/sage",
       "worker_count": 1, "wall_cap_seconds": 590,
       "rss_cap_bytes": 4294967296,
       "sources": {name: {"path": str(path), "sha256": sha(path)}
                   for name, path in sources.items()}}
protocol.write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": cfg["status"], "protocol_sha256": sha(protocol)}, sort_keys=True))
