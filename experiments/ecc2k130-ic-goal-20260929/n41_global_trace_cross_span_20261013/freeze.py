import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
prior = HERE.parent / "n41_bilinear_rank_screen_20261013"
sources = [HERE / "census.cpp", HERE / "census", HERE / "run.py",
           HERE / "sage_runtime_info.json",
           prior / "native.cpp", prior / "protocol.json"]
protocol = {
    "status": "FROZEN", "kind": "n41_complete_product_family_cross_span",
    "candidate_id": None, "curve_id": "EC1N41Ckb1h023d9a38bbf7",
    "field_modulus": "t^41+t^3+1",
    "public_target_reciprocal": 1000731834126,
    "product_families": 2048, "worker_count": 1,
    "wall_cap_seconds": 120, "rss_cap_bytes": 4294967296,
    "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
}
with (HERE / "protocol.json").open("x") as stream:
    json.dump(protocol, stream, indent=2, sort_keys=True)
    stream.write("\n")
