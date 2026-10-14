import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
prior = HERE.parent / "n41_bilinear_rank_screen_20261013"
sources = [HERE / "lowrank.cpp", HERE / "lowrank", HERE / "run.py",
           prior / "native.cpp", prior / "protocol.json", prior / "sage_result.json"]
protocol = {
    "status": "FROZEN",
    "kind": "n41_lowrank_trace_joint_two_free_output_families",
    "candidate_id": None,
    "curve_id": "EC1N41Ckb1h023d9a38bbf7",
    "field_modulus": "t^41+t^3+1",
    "constructed_target_reciprocal": 1515824644274,
    "public_target_reciprocal": 1000731834126,
    "positive_product_families": [819, 176],
    "additional_public_family_pairs": 30,
    "family_pair_selection_seed": 202610131700,
    "projection_selection_seed_base": 202610131701,
    "selected_independent_projections_per_case": 12,
    "low_cross_rank_ceiling": 3,
    "max_lambda_trials_per_case": 200000,
    "worker_count": 1,
    "wall_cap_seconds": 120,
    "rss_cap_bytes": 4294967296,
    "sources": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
}
with (HERE / "protocol.json").open("x") as stream:
    json.dump(protocol, stream, indent=2, sort_keys=True)
    stream.write("\n")
