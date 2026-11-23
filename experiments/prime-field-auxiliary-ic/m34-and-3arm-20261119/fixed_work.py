"""Recompute fixed-work timing floors in integer nanoseconds from the pinned E1 archive."""
import csv
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys

here = Path(__file__).resolve().parent
blob = "f1155baab307d9434d840cae139a1f90a3703b33"
raw = subprocess.check_output(["git", "cat-file", "blob", blob], cwd=here)
data = json.loads(raw, parse_float=Decimal)
assert data["protocol_sha256"] == "5aa4f11447fd3f9a94142c4cf0fb1e2591f4ccb2a853d6539d1efc2a9f6d448d"
targets = {r["target_id"]: r for r in data["e1_m2_5target_solves"]}
assert set(targets) == {f"E1_T{i}" for i in range(5)}
rows = [(t,2,name,r) for t,v in targets.items() for name,r in v["arms"].items()]
rows += [("E1_T0",int(m[1:]),name,r) for m,arms in data["e1_m3_m4_solves_T0"].items()
         for name,r in arms.items()]

def ns(value, scale):
    result = value*scale
    assert result == int(result)
    return int(result)

# The archived arm A supplies the per-target, per-arity panel reference.
rho = {}
panel_rho = {}
for target,arity,name,r in rows:
    assert r["status"] == "solved" and r["summands"] == arity
    assert r["scalar"] == targets[target]["recovered_scalar"] and r["false_relations"] == 0
    if "rho" in r:
        ref = r["rho"]
        assert ref["scalar"] == r["scalar"]
        observed = ns(ref["online_ms"],10**6)
        assert (target,arity) not in panel_rho
        panel_rho[target,arity] = observed
        rho[target] = max(rho.get(target,0), observed)

writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(["target","arity","arm","total_ns","decomposition_ns","residual_lower_ns",
                 "residual_upper_ns","panel_rho_upper_ns","slowest_rho_upper_ns","slowest_floor_exceeds"])
for target,arity,name,r in rows:
    total = ns(r["ic_observed_total_s"],10**9)
    decomp = ns(r["decomposition_s"],10**9)
    # Each seconds field is rounded to four decimal places; the difference
    # can shift by 100 us. The rho milliseconds field can shift by 50 ns.
    lo, hi = max(0,total-decomp-100000), total-decomp+100000
    upper = rho[target]+50
    assert hi >= lo
    writer.writerow([target,arity,name,total,decomp,lo,hi,panel_rho[target,arity]+50,
                     upper,int(lo > upper)])
