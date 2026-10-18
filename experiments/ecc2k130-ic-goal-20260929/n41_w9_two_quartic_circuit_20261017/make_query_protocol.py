"""Freeze the unpinned one-worker public N41 query."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
root=here.parent
solver=Path("/opt/homebrew/Cellar/cryptominisat/5.14.7/bin/cryptominisat5")
paths=[here/name for name in ("query.py","build.py","build_protocol.json",
                              "build_result.json","formula.xcnf","input_wires.json",
                              "bezout_result.json","sage_runtime_info.json")]
paths += [root/"n41_w9_two_quartic_resultant_20261017/panel.json",solver]
assert solver.is_file() and not (here/"query_protocol.json").exists()
build=json.loads((here/"build_result.json").read_text())
assert build["status"]=="PASS_N41_TWO_QUARTIC_BEZOUT_CIRCUIT"
out={"status":"FROZEN_BEFORE_UNPINNED_BEZOUT_QUERY",
     "candidate_id":None,"curve_id":build["curve_id"],
     "public_point":build["public_point"],
     "input_law":"same frozen N41 public point; all five source-pair codes and preceding reciprocal free; exact characteristic-two Bezout resultant eliminates intermediate reciprocal",
     "worker_count":1,"solver":str(solver),
     "solver_cap_seconds":590,"parent_wall_cap_seconds":600,
     "rss_cap_bytes":4*1024**3,
     "launch_command":f"/Volumes/SSD990/cryptanalysis/sage -python {here/'query.py'}",
     "sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths}}
(here/"query_protocol.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
