"""Freeze the unpinned one-worker N41 two-quadratic query."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
root=here.parent
solver=Path("/opt/homebrew/Cellar/cryptominisat/5.14.7/bin/cryptominisat5")
paths=[here/name for name in ("query.py","build.py","build_protocol.json",
                              "build_result.json","formula.xcnf","input_wires.json",
                              "probe_protocol.json","probe_result.json",
                              "audit_protocol.json","audit_result.json",
                              "replay_model_sage.py","sage_runtime_info.json")]
paths += [root/"n41_w9_two_quartic_resultant_20261017/panel.json",solver]
assert solver.is_file() and not (here/"query_protocol.json").exists()
build=json.loads((here/"build_result.json").read_text())
assert build["status"]=="PASS_N41_FINAL_PAIR_QUADRATICS_CIRCUIT"
probe=json.loads((here/"probe_result.json").read_text())["arm_results"]
assert [row["arm"] for row in probe]==["direct","quadratic","quadratic","direct"]
assert all(row["status"]=="INDETERMINATE_CONFLICT_CAP" for row in probe)
assert all(probe[i]["reported_decisions"]/probe[j]["reported_decisions"]<=.8
           and probe[i]["wall_seconds"]/probe[j]["wall_seconds"]<=1.25
           for i,j in ((1,0),(2,3)))
out={"status":"FROZEN_BEFORE_UNPINNED_FINAL_PAIR_QUADRATICS_QUERY",
     "candidate_id":None,"curve_id":build["curve_id"],
     "public_point":build["public_point"],
     "input_law":"same frozen N41 public point; all five source-pair codes, preceding reciprocal, final pair-output reciprocal and shared target root free; source pair quadratic and target S3 quadratic",
     "worker_count":1,"solver":str(solver),
     "solver_cap_seconds":590,"parent_wall_cap_seconds":600,
     "rss_cap_bytes":4*1024**3,
     "launch_command":f"/Volumes/SSD990/cryptanalysis/sage -python {here/'query.py'}",
     "sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths}}
(here/"query_protocol.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
