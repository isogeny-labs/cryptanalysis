"""Freeze the universal GF(2) resultant ideal-membership check."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
path = HERE / "redundancy_protocol.json"
assert not path.exists()
sources = {
    "script": HERE / "test_redundancy_sage.py",
    "source_reduction": ROOT / "n41_w9_quadratic_joint_resultant_20261023/reduction_result.json",
    "direct_resultant_build": ROOT / "n41_w9_quadratic_joint_resultant_20261023/build_result.json",
    "frozen_probe": ROOT / "n41_w9_quadratic_joint_resultant_20261023/probe_result.json",
    "sage_runtime": HERE / "sage_runtime_info.json",
}
cfg = {
    "status": "FROZEN_BEFORE_UNIVERSAL_RESULTANT_REDUNDANCY_CHECK",
    "candidate_id": None,
    "wall_cap_seconds": 120,
    "rss_cap_bytes": 4294967296,
    "script_sha256": sha(sources["script"]),
    "sources": {name: {"path": str(source), "sha256": sha(source)} for name, source in sources.items()},
}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": cfg["status"], "protocol_sha256": sha(path)}, sort_keys=True))
