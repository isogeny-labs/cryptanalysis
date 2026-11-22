"""Freeze a fully deferred control before formula construction."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
path = HERE / "relaxed_build_protocol.json"
assert not path.exists()
base = json.loads((HERE / "build_result.json").read_text())
assert base["status"] == "PASS_N41_SIXPAIR_DEFERRED_CIRCUIT"
sources = {
    "builder": HERE / "build_relaxed.py",
    "freeze": Path(__file__),
    "circuit": HERE / "circuit_deferred.py",
    "prior_build_result": HERE / "build_result.json",
    "public_relation": ROOT / "n41_w8_sixpair_sat_20261016/join_audit_result.json",
    "runtime": HERE / "sage_runtime_info.json",
}
cfg = {"status": "FROZEN_BEFORE_N41_ALL_DEFERRED_BUILD",
       "candidate_id": None, "curve_id": base["curve_id"],
       "exact_slots": [], "deferred_slots": [0, 1, 2, 3, 4, 5],
       "sources": {name: {"path": str(source), "sha256": sha(source)}
                   for name, source in sources.items()}}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": cfg["status"], "protocol_sha256": sha(path)}, sort_keys=True))
