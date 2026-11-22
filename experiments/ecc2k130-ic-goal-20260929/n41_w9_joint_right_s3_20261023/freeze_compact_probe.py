"""Freeze an ABBA conflict-capped test of the compact joint S3 circuit."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/"n41_w9_final_pair_quadratics_20261018"
SOLVER=Path("/opt/homebrew/Cellar/cryptominisat/5.14.7/bin/cryptominisat5")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


build=json.loads((HERE/"compact_build_result.json").read_text())
baseline=json.loads((BASE/"build_result.json").read_text())
assert build["status"]=="PASS_N41_COMPACT_JOINT_RIGHT_S3_CIRCUIT"
assert baseline["status"]=="PASS_N41_FINAL_PAIR_QUADRATICS_CIRCUIT"
assert build["public_point"]==baseline["public_point"]
sources={str(path):sha(path) for path in
         (HERE/"probe_compact.py",HERE/"compact_build_result.json",
          HERE/"compact_build_protocol.json",HERE/"compact_formula.xcnf",
          HERE/"join_rows.json",HERE/"probe_result.json",
          BASE/"build_result.json",BASE/"formula.xcnf",SOLVER)}
protocol={"status":"FROZEN_BEFORE_COMPACT_JOINT_S3_ABBA_PROBE",
          "candidate_id":None,"curve_id":build["curve_id"],
          "public_point":build["public_point"],
          "formulas":{"baseline":str(BASE/"formula.xcnf"),
                      "compact":str(HERE/"compact_formula.xcnf")},
          "arms":["baseline","compact","compact","baseline"],
          "solver":str(SOLVER),"worker_count":1,"max_conflicts":20000,
          "solver_wall_cap_seconds":170,"parent_wall_cap_seconds":180,
          "rss_cap_bytes":4*1024**3,"sources":sources,
          "promotion_gate":"Both compact arms terminal at the same conflict cap with healthy monitors, at most 90 percent of adjacent baseline decisions and at most 125 percent of adjacent baseline wall; otherwise retain a stage result without promotion."}
assert not (HERE/"compact_probe_protocol.json").exists()
with (HERE/"compact_probe_protocol.json").open("x") as out:
    json.dump(protocol,out,sort_keys=True,indent=2)
    out.write("\n")
print(json.dumps({"status":protocol["status"],"max_conflicts":protocol["max_conflicts"]}))
