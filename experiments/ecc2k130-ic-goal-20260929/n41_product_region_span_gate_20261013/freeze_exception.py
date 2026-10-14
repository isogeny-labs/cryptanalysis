import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
prior = HERE.parent / "n41_bilinear_rank_screen_20261013"
sources = [HERE / name for name in ("exception.cpp", "exception", "region_core.hpp",
                                     "run_exception.py", "protocol.json",
                                     "audit_result.json", "sage_runtime_info.json")]
sources.append(prior / "native.cpp")
protocol = {
    "status": "FROZEN", "kind": "n41_four_family_exceptional_region_cross_span",
    "curve_id": "EC1N41Ckb1h023d9a38bbf7",
    "product_codes": [0, 1, 2, 3],
    "public_target_reciprocal": 1000731834126,
    "worker_count": 1, "wall_cap_seconds": 120,
    "rss_cap_bytes": 4294967296,
    "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sources},
}
with (HERE / "exception_protocol.json").open("x") as stream:
    json.dump(protocol, stream, indent=2, sort_keys=True)
    stream.write("\n")
