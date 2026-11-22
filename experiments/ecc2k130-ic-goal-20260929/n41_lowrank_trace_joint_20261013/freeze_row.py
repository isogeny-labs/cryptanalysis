import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
prior = HERE.parent / "n41_bilinear_rank_screen_20261013"
sources = [HERE / name for name in ("rowkernel.cpp", "rowkernel", "lowrank_core.hpp",
                                     "run_row.py", "protocol.json", "cases.jsonl",
                                     "audit_result.json")]
sources.append(prior / "native.cpp")
protocol = {
    "status": "FROZEN", "kind": "n41_deterministic_row_kernel_trace_joint",
    "candidate_id": None, "curve_id": "EC1N41Ckb1h023d9a38bbf7",
    "public_target_reciprocal": 1000731834126,
    "constructed_target_reciprocal": 1515824644274,
    "family_panel_from_protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
    "selected_independent_projections_per_case": 12,
    "cross_rank_ceiling": 1,
    "one_free_cross_row_per_kernel": True,
    "worker_count": 1, "wall_cap_seconds": 120,
    "rss_cap_bytes": 4294967296,
    "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sources},
}
with (HERE / "row_protocol.json").open("x") as stream:
    json.dump(protocol, stream, indent=2, sort_keys=True)
    stream.write("\n")
