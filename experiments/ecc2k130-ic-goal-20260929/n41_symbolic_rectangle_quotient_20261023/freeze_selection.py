"""Freeze disjoint training and holdout rectangles for adaptive bit order."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCES = {
    "rectangle_protocol": HERE / "protocol_v2.json",
    "rectangle_result": HERE / "result_v2.json",
    "rectangle_audit": HERE / "audit_result_v2.json",
    "coordinate_audit": ROOT / "n41_w8_two_code_affine_span_20261013/cases.jsonl",
    "target_residuals": ROOT / "n41_two_pair_affine_router_20261014/targets.bin",
    "feature_source": ROOT / "n41_target_conditioned_family_20261015/cubic_screen.py",
    "inverse_source": ROOT / "n41_target_conditioned_family_20261015/reciprocal_cubic.py",
    "selection_source": HERE / "select_bits.py",
    "freeze_source": HERE / "freeze_selection.py",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


record = {
    "status": "FROZEN_N41_CUBIC_BIT_SELECTION",
    "candidate_id": None,
    "train_rectangles": 32,
    "holdout_rectangles": 100,
    "max_bits": 16,
    "wall_cap_seconds": 120,
    "rss_cap_bytes": 4 * 1024**3,
    "selection_rule": "Greedy cover of full-feature training mismatches, maximizing still-uncovered rectangles with lowest feature index breaking ties. Holdout roots are read only after the order is fixed.",
    "sources": {name: {"path": str(path), "sha256": sha(path)}
                for name, path in SOURCES.items()},
}
assert not (HERE / "selection_protocol.json").exists()
(HERE / "selection_protocol.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
