"""Freeze the root/direct/direct/root fixed-conflict comparison."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
root=here.parent
baseline=root/"n41_w9_root_witness_20261017"
solver=Path("/opt/homebrew/Cellar/cryptominisat/5.14.7/bin/cryptominisat5")
formulas={"root":baseline/"formula.xcnf","direct":here/"formula.xcnf"}
paths=[here/name for name in ("probe.py","build.py","build_protocol.json",
                              "build_result.json","sage_runtime_info.json")]
paths += [baseline/name for name in ("formula.xcnf","build_result.json")]
paths += [root/"n41_w9_bezout_kernel_20261017/kernel_result.json"]
paths += [solver]
assert solver.is_file() and not (here/"probe_protocol.json").exists()
old=json.loads((baseline/"build_result.json").read_text())
new=json.loads((here/"build_result.json").read_text())
assert old["curve_id"]==new["curve_id"]
assert old["public_point"]==new["public_point"]
assert new["status"]=="PASS_N41_DIRECT_ROOT_CIRCUIT"
out={"status":"FROZEN_BEFORE_ABBA_DIRECT_PROBE",
     "candidate_id":None,"curve_id":new["curve_id"],"public_point":new["public_point"],
     "arms":["root","direct","direct","root"],
     "worker_count":1,"max_conflicts":20000,
     "solver_wall_cap_seconds":170,"parent_wall_cap_seconds":180,
     "rss_cap_bytes":4*1024**3,"solver":str(solver),
     "formulas":{name:str(path) for name,path in formulas.items()},
     "promotion_gate":"All arms finish the conflict cap with monitors passing; each direct arm has at most 80 percent of its adjacent root arm decisions and no more than 125 percent of its adjacent root arm wall before a full N41 query.",
     "sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths}}
(here/"probe_protocol.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
