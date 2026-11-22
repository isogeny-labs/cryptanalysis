"""Freeze the fully deferred N41 query before solver execution."""
import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
path = HERE / "relaxed_query_protocol.json"
assert not path.exists()
build = json.loads((HERE / "relaxed_build_result.json").read_text())
assert build["status"] == "PASS_N41_ALL_DEFERRED_CIRCUIT"
solver = shutil.which("cryptominisat5")
assert solver
sources = {
    "query": HERE / "query_relaxed.py",
    "freeze": Path(__file__),
    "formula": HERE / "n41_public_all_deferred.xcnf",
    "build_result": HERE / "relaxed_build_result.json",
    "build_protocol": HERE / "relaxed_build_protocol.json",
    "public_relation": ROOT / "n41_w8_sixpair_sat_20261016/join_audit_result.json",
    "runtime": HERE / "sage_runtime_info.json",
    "solver": Path(solver),
}
cfg = {"status": "FROZEN_BEFORE_N41_ALL_DEFERRED_QUERY",
       "candidate_id": None, "curve_id": build["curve_id"],
       "public_point": build["public_point"],
       "worker_count": 1, "solver": solver,
       "solver_wall_cap_seconds": 110,
       "parent_wall_cap_seconds": 120,
       "rss_cap_bytes": 4294967296,
       "sources": {name: {"path": str(source), "sha256": sha(source)}
                   for name, source in sources.items()}}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": cfg["status"], "protocol_sha256": sha(path)}, sort_keys=True))
