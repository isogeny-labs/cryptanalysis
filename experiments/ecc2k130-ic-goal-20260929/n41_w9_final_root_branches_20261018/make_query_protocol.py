"""Freeze the exploratory unpinned one-worker N41 selector query."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
root=here.parent
solver=Path("/opt/homebrew/Cellar/cryptominisat/5.14.7/bin/cryptominisat5")
paths=[here/name for name in ("query.py","build.py","build_protocol.json",
                              "build_result.json","formula.xcnf","input_wires.json",
                              "probe_protocol.json","probe_result.json",
                              "holdout_protocol.json","holdout_result.json",
                              "replay_model_sage.py","sage_runtime_info.json")]
paths += [root/"n41_w9_two_quartic_resultant_20261017/panel.json",
          root/"n41_w9_target_w_bdd_20261017/w_table.json",
          root/"n41_w9_target_w_bdd_20261017/audit_result.json",solver]
assert solver.is_file() and not (here/"query_protocol.json").exists()
build=json.loads((here/"build_result.json").read_text())
assert build["status"]=="PASS_N41_FINAL_ROOT_SELECTOR_CIRCUIT"
holdout=json.loads((here/"holdout_result.json").read_text())["arm_results"]
assert [row["arm"] for row in holdout]==["direct","selector","selector","direct"]
assert all(row["status"]=="INDETERMINATE_CONFLICT_CAP" for row in holdout)
assert max(holdout[1]["wall_seconds"],holdout[2]["wall_seconds"])/min(holdout[1]["wall_seconds"],holdout[2]["wall_seconds"])>1.25
out={"status":"FROZEN_BEFORE_EXPLORATORY_SELECTOR_QUERY",
     "candidate_id":None,"curve_id":build["curve_id"],
     "public_point":build["public_point"],
     "input_law":"same frozen N41 public point; first four source-pair codes, preceding reciprocal and nine-bit final code/root selector free; exact 284-row final-pair table",
     "promotion_status":"holdout wall ratios passed but selector A/A noise gate failed; this query is exploratory relation search, not an admitted timing comparison",
     "worker_count":1,"solver":str(solver),
     "solver_cap_seconds":590,"parent_wall_cap_seconds":600,
     "rss_cap_bytes":4*1024**3,
     "launch_command":f"/Volumes/SSD990/cryptanalysis/sage -python {here/'query.py'}",
     "sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths}}
(here/"query_protocol.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
