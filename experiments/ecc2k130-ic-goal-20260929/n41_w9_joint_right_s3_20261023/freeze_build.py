"""Freeze the joint-association circuit and exact source dependencies."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/"n41_w9_final_pair_quadratics_20261018"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


prior=json.loads((BASE/"build_protocol.json").read_text())
sources=dict(prior["sources"])
for path in (HERE/"build.py",HERE/"join_rows.json",HERE/"freeze_sage.py",
             HERE/"sage_runtime_info.json",HERE/"freeze_failure_v1.json",
             BASE/"build_protocol.json"):
    sources[str(path)]=sha(path)
protocol={"status":"FROZEN_BEFORE_JOINT_RIGHT_S3_BUILD",
          "candidate_id":None,"curve_id":prior["curve_id"],
          "states":prior["states"],"fixture":prior["fixture"],
          "panel":prior["panel"],"join_rows":str(HERE/"join_rows.json"),
          "sources":sources,"wall_cap_seconds":300,
          "memory_envelope_bytes":4*1024**3,
          "method":"baseline final-pair quadratic circuit plus preceding pair root and alternate right-two-pair S3 target link"}
assert not (HERE/"build_protocol.json").exists()
with (HERE/"build_protocol.json").open("x") as out:
    json.dump(protocol,out,sort_keys=True,indent=2)
    out.write("\n")
print(json.dumps({"status":protocol["status"],"sources":len(sources)}))
