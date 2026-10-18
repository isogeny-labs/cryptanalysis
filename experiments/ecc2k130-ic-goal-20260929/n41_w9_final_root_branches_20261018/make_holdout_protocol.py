"""Freeze a fresh 50,000-conflict wall-time holdout before its solver arms."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
root=here.parent
baseline=root/"n41_w9_direct_root_20261017"
solver=Path("/opt/homebrew/Cellar/cryptominisat/5.14.7/bin/cryptominisat5")
formulas={"direct":baseline/"formula.xcnf","selector":here/"formula.xcnf"}
paths=[here/name for name in ("holdout.py","build.py","build_protocol.json",
                              "build_result.json","probe_protocol.json","probe_result.json",
                              "sage_runtime_info.json")]
paths += [baseline/name for name in ("formula.xcnf","build_result.json")]
paths += [root/"n41_w9_target_w_bdd_20261017/audit_result.json",
          root/"n41_w9_target_w_bdd_20261017/w_table.json"]
paths += [solver]
assert solver.is_file() and not (here/"holdout_protocol.json").exists()
old=json.loads((baseline/"build_result.json").read_text())
new=json.loads((here/"build_result.json").read_text())
assert old["curve_id"]==new["curve_id"]
assert old["public_point"]==new["public_point"]
assert new["status"]=="PASS_N41_FINAL_ROOT_SELECTOR_CIRCUIT"
out={"status":"FROZEN_BEFORE_ABBA_SELECTOR_HOLDOUT",
     "candidate_id":None,"curve_id":new["curve_id"],"public_point":new["public_point"],
     "arms":["direct","selector","selector","direct"],
     "worker_count":1,"max_conflicts":50000,
     "solver_wall_cap_seconds":240,"parent_wall_cap_seconds":250,
     "rss_cap_bytes":4*1024**3,"solver":str(solver),
     "formulas":{name:str(path) for name,path in formulas.items()},
     "promotion_gate":"All arms finish 50000 conflicts with monitors passing; each selector/direct adjacent wall ratio is at most 0.75, and the same-formula A/A wall ratio in either direction is at most 1.25 for both formulas before a full N41 query.",
     "sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths}}
(here/"holdout_protocol.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
