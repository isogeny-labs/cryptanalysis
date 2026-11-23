"""Freeze the ABBA fixed-conflict comparison before any solver arm."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
root=here.parent
det=root/"n41_w9_two_quartic_circuit_20261017"
solver=Path("/opt/homebrew/Cellar/cryptominisat/5.14.7/bin/cryptominisat5")
formulas={"determinant":det/"formula.xcnf","kernel":here/"formula.xcnf"}
paths=[here/name for name in ("probe.py","build.py","build_protocol.json",
                              "build_result.json","kernel_result.json","sage_runtime_info.json")]
paths += [det/name for name in ("formula.xcnf","build_result.json")]
paths += [solver]
assert solver.is_file() and not (here/"probe_protocol.json").exists()
old=json.loads((det/"build_result.json").read_text())
new=json.loads((here/"build_result.json").read_text())
assert old["curve_id"]==new["curve_id"]
assert old["public_point"]==new["public_point"]
assert new["status"]=="PASS_N41_BEZOUT_KERNEL_CIRCUIT"
out={"status":"FROZEN_BEFORE_ABBA_KERNEL_PROBE",
     "candidate_id":None,"curve_id":new["curve_id"],"public_point":new["public_point"],
     "arms":["determinant","kernel","kernel","determinant"],
     "worker_count":1,"max_conflicts":20000,
     "solver_wall_cap_seconds":170,"parent_wall_cap_seconds":180,
     "rss_cap_bytes":4*1024**3,"solver":str(solver),
     "formulas":{name:str(path) for name,path in formulas.items()},
     "promotion_gate":"Both kernel arms finish the conflict cap, each uses at most 80 percent of its adjacent determinant arm wall, and all four monitors pass before a full N41 query.",
     "sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths}}
(here/"probe_protocol.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
