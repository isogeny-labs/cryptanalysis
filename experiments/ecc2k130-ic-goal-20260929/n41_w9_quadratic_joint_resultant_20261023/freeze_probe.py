"""Freeze one-worker ABBA between explicit-y and eliminated-y circuits."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / "n41_w9_joint_right_s3_20261023"
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
path = HERE / "probe_protocol.json"
assert not path.exists()
build = json.loads((HERE / "build_result.json").read_text())
monitor = json.loads((HERE / "build_supervisor.json").read_text())
assert build["status"] == monitor["status"] == "PASS_N41_QUADRATIC_JOINT_RESULTANT_CIRCUIT"
assert monitor["result_sha256"] == sha(HERE / "build_result.json")
old = json.loads((PRIOR / "compact_build_result.json").read_text())
assert old["status"] == "PASS_N41_COMPACT_JOINT_RIGHT_S3_CIRCUIT"
solver = Path("/opt/homebrew/Cellar/cryptominisat/5.14.7/bin/cryptominisat5")
assert solver.exists()
formulas = {"explicit_y": PRIOR / "compact_formula.xcnf",
            "resultant": HERE / "resultant_formula.xcnf"}
assert sha(formulas["explicit_y"]) == old["formula_sha256"]
assert sha(formulas["resultant"]) == build["formula_sha256"]
sources = {HERE / "probe.py", Path(__file__), HERE / "build_result.json",
           HERE / "build_supervisor.json", HERE / "build_run_protocol.json",
           HERE / "preflight_result.json", PRIOR / "compact_build_result.json",
           PRIOR / "compact_retry_result.json", solver, *formulas.values()}
cfg = {"status": "FROZEN_BEFORE_QUADRATIC_RESULTANT_ABBA",
       "candidate_id": None, "curve_id": build["curve_id"],
       "public_point": build["public_point"],
       "solver": str(solver), "formulas": {k: str(v) for k, v in formulas.items()},
       "arms": ["explicit_y", "resultant", "resultant", "explicit_y"],
       "worker_count": 1, "max_conflicts": 20000,
       "solver_wall_cap_seconds": 170, "parent_wall_cap_seconds": 180,
       "rss_cap_bytes": 4294967296,
       "promotion_gate": "Both resultant arms terminal at the same conflict cap with healthy monitors, at most 90 percent of adjacent explicit-y decisions and at most 125 percent of adjacent explicit-y wall; otherwise retain a stage result without full-query promotion.",
       "sources": {str(source): sha(source) for source in sources}}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": cfg["status"], "protocol_sha256": sha(path)}, sort_keys=True))
