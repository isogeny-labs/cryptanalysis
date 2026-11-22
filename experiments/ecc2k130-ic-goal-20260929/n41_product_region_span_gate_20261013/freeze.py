import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
prior = HERE.parent / "n41_bilinear_rank_screen_20261013"
sources = [HERE / "regions.cpp", HERE / "regions", HERE / "run.py",
           HERE / "sage_runtime_info.json", prior / "native.cpp", prior / "protocol.json"]
protocol = {
    "status": "FROZEN", "kind": "n41_target_conditioned_product_region_span_gate",
    "candidate_id": None, "curve_id": "EC1N41Ckb1h023d9a38bbf7",
    "field_modulus": "t^41+t^3+1",
    "public_target_reciprocal": 1000731834126,
    "constructed_target_reciprocal": 1515824644274,
    "product_family_count": 2048,
    "free_bit_levels": list(range(12)),
    "sampled_pairs_per_tested_level": 512,
    "sampled_levels": [0, 1, 2, 3],
    "sampling_seed_base": 202610131800,
    "worker_count": 1, "wall_cap_seconds": 120,
    "rss_cap_bytes": 4294967296,
    "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
}
with (HERE / "protocol.json").open("x") as stream:
    json.dump(protocol, stream, indent=2, sort_keys=True)
    stream.write("\n")
