"""Pin the complete fourth-axis exact join and resource envelope."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCES = {
    "geometry": ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json",
    "coordinate_audit": ROOT / "n41_w8_two_code_affine_span_20261013/cases.jsonl",
    "target_table": HERE / "target_table.json",
    "witness_protocol": ROOT / "n41_w8_fixedseed_ordinary_join_20261013/protocol.json",
    "sage_curve_audit": ROOT / "n41_w8_fixed_sum_table_20261009/audit.py",
    "sage_runtime": HERE / "sage_runtime_info.json",
    "producer": HERE / "full_traversal_sage.py",
    "freeze": HERE / "freeze_traversal.py",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


geo = json.loads(SOURCES["geometry"].read_text())
record = {"status": "FROZEN_N41_FULL_FOUR_AXIS_TRAVERSAL",
          "candidate_id": None, "curve_id": geo["curve_id"],
          "suffix_state_ids": [14, 109, 51],
          "case_rows": 1554, "eligible_quads": 1386816,
          "worker_count": 1, "wall_cap_seconds": 600,
          "rss_cap_bytes": 4*1024**3,
          "sources": {name: {"path": str(path), "sha256": sha(path)}
                      for name, path in SOURCES.items()}}
assert not (HERE / "traversal_protocol.json").exists()
(HERE / "traversal_protocol.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
