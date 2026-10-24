"""Freeze the independent 960-state source-sign audit."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
path = HERE / "source_sign_audit_protocol.json"
assert not path.exists()
sources = {
    "audit": HERE / "audit_source_signs.py",
    "freeze": Path(__file__),
    "geometry": ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json",
    "replay": ROOT / "n41_basis_aware_quartic_20261011/replay.py",
    "runtime": HERE / "sage_runtime_info.json",
}
cfg = {"status": "FROZEN_BEFORE_N41_SOURCE_SIGN_AUDIT",
       "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
       "expected_states": 960, "expected_root_sign_pairs": 480,
       "sources": {name: {"path": str(source), "sha256": sha(source)}
                   for name, source in sources.items()}}
path.write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n")
print(cfg["status"])
