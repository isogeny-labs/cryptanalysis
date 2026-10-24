"""Freeze the negative and witness depth-six code rectangles before execution."""
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
    "prior_region_result": ROOT / "n41_target_conditioned_family_20261015/reciprocal_result.json",
    "prior_quotient_result": ROOT / "n41_quotient_trace_cubic_20261023/result.json",
    "field_arithmetic": Path("/Volumes/SSD990/crypto/research/sat_factor_base_review_20260908/autolab_orbit_extract_20260924/independent_replay.py"),
    "sage_curve_audit": ROOT / "n41_w8_fixed_sum_table_20261009/audit.py",
    "sage_runtime": HERE / "sage_runtime_info.json",
    "producer": HERE / "run.py",
    "auditor": HERE / "audit_sage.py",
    "freeze": HERE / "freeze.py",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


record = {
    "status": "FROZEN_N41_TWO_CODE_RECTANGLE_QUOTIENT",
    "candidate_id": None,
    "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
    "field_degree": 41,
    "field_modulus": [41, 3, 0],
    "target_residual_index": 0,
    "code_prefix_depth": [6, 6],
    "bit_indices": [2, 5, 8],
    "feature_index": 1597,
    "rectangles": [
        {"label": "rejecting", "prefix": [0, 4], "case_indices": [4, 5, 43, 44]},
        {"label": "witness", "prefix": [38, 53], "case_indices": [965, 966, 1004, 1005]},
    ],
    "selection": "Two archived full 2x2 rectangles selected before symbolic execution: one cubic-bit mismatch and the known public witness control.",
    "worker_count": 1,
    "wall_cap_seconds": 300,
    "rss_cap_bytes": 4 * 1024**3,
    "sources": {name: {"path": str(path), "sha256": sha(path)}
                for name, path in SOURCES.items()},
}
assert not (HERE / "protocol.json").exists()
(HERE / "protocol.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
