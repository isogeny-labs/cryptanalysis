"""Freeze a root-free quotient trace panel before reading coordinate outcomes."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCES = {
    "geometry": ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json",
    "root_polynomial": ROOT / "n41_w8_three_pair_resultant_20261013/result.json",
    "coordinate_audit": ROOT / "n41_w8_two_code_affine_span_20261013/cases.jsonl",
    "target_residuals": ROOT / "n41_two_pair_affine_router_20261014/targets.bin",
    "field_arithmetic": Path("/Volumes/SSD990/crypto/research/sat_factor_base_review_20260908/autolab_orbit_extract_20260924/independent_replay.py"),
    "producer": HERE / "run.py",
    "auditor": HERE / "audit.py",
    "sage_curve_audit": ROOT / "n41_w8_fixed_sum_table_20261009/audit.py",
    "sage_runtime": HERE / "sage_runtime_info.json",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


panel = [0, 1, 7, 31, 255, 766, 966, 1553]
record = {
    "status": "FROZEN_BEFORE_N41_QUOTIENT_CUBIC",
    "candidate_id": None,
    "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
    "field_degree": 41,
    "field_modulus": [41, 3, 0],
    "panel_indices": panel,
    "witness_index": 966,
    "feature_definition": "z0; zi*zj for 1<=i<j<=40; zi*zj*zk for 1<=i<j<k<=40",
    "feature_width": 10661,
    "worker_count": 1,
    "wall_cap_seconds": 300,
    "rss_cap_bytes": 4 * 1024**3,
    "sources": {name: {"path": str(path), "sha256": sha(path)}
                for name, path in SOURCES.items()},
}
assert not (HERE / "protocol.json").exists()
(HERE / "protocol.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
