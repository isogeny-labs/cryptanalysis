"""Freeze same-row block-norm scaling after the N41 and N131 gates."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
protocol = HERE / "protocol_scaling.json"
assert not protocol.exists()
for case in ("n41", "n131"):
    result = json.loads((HERE / f"{case}_result.json").read_text())
    supervisor = json.loads((HERE / f"{case}_supervisor.json").read_text())
    assert result["status"] == supervisor["status"] == f"PASS_{case.upper()}_BLOCK_NORM_GATE"
    assert supervisor["result_sha256"] == sha(HERE / f"{case}_result.json")
sources = {"script": HERE / "scaling_sage.py",
           "supervisor": HERE / "supervise_scaling.py",
           "freeze_script": Path(__file__),
           "runtime": HERE / "sage_runtime_info.json",
           "n41_result": HERE / "n41_result.json",
           "n41_supervisor": HERE / "n41_supervisor.json",
           "n131_result": HERE / "n131_result.json",
           "n131_supervisor": HERE / "n131_supervisor.json",
           "coefficients": ROOT / "n131_w33_freecode_resultant_20261018/coefficients.json",
           "reference": ROOT / "n131_native_quartic_filter_20261019/reference_result.json"}
cfg = {"status": "FROZEN_BEFORE_N131_BLOCK_NORM_SCALING",
       "curve_id": "EC1N131Ckb1heb5f1998f20b", "candidate_id": None,
       "target_indexes": [0, 1], "block_sizes": [4, 8, 16, 32, 64],
       "sage_launcher": "/Volumes/SSD990/cryptanalysis/sage",
       "worker_count": 1, "worker_alarm_seconds": 560,
       "wall_cap_seconds": 590, "rss_cap_bytes": 4294967296,
       "sources": {name: {"path": str(path), "sha256": sha(path)}
                   for name, path in sources.items()}}
protocol.write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": cfg["status"], "protocol_sha256": sha(protocol)}, sort_keys=True))
