"""Independent Sage enumeration and matrix-rank replay for the 40-point fiber."""
from pathlib import Path
from sage.all import GF, QQ, EllipticCurve, matrix
import gzip
import hashlib
import itertools
import json

H = Path(__file__).resolve().parent
inp = json.loads((H/"archived-inputs.json").read_text())
result = json.loads((H/"result.json").read_text())
p = 317
F = GF(p)
E = EllipticCurve(F,[0,-1,1,-10,-20])
assert E.cardinality() == 305
raw_points = inp["class_points"]+[[16,60]]
points = [E(F(x),F(y)) for x,y in raw_points]
assert len(points) == len(set(points)) == 40
assert points[-1] == E(16,60)
assert 305*points[-1] == E(0)
assert points[-1].order() == 5

def unpack_rows(name):
    return [{int(i):int(v) for i,v in r.items()} for r in inp[name]]

base = unpack_rows("base_rows")
closed = unpack_rows("closed_rows")
short = unpack_rows("short_cancellation_rows")
for row in base+closed+short:
    assert sum((c*points[i] for i,c in row.items()),E(0)) == E(0)

rows = [json.loads(s) for s in gzip.open(H/"direct-rows.jsonl.gz","rt")]
assert len(rows) == sum(result["candidate_counts"].values())
saved = [(tuple(r["indices"]),tuple(r["coefficients"])) for r in rows]
enumerated = []
for support in range(1,4):
    for inds in itertools.combinations(range(40),support):
        for tail in itertools.product((-1,1),repeat=support-1):
            coeffs = (1,)+tail
            if sum((c*points[i] for i,c in zip(inds,coeffs)),E(0)) == E(0):
                enumerated.append((inds,coeffs))
assert enumerated == saved
direct = [dict(zip(inds,coeffs)) for inds,coeffs in saved]

def sage_rank(rows,base_ring):
    M = matrix(base_ring,len(rows),40)
    for k,row in enumerate(rows):
        for i,c in row.items():
            M[k,i] = c
    return int(M.rank())

families = {"archived_base":base,"archived_base_closed":base+closed,
            "archived_all":base+closed+short,"direct_only":direct,
            "archived_all_plus_direct":base+closed+short+direct}
ranks = {name:{"QQ":sage_rank(r,QQ),"F61":sage_rank(r,GF(61))} for name,r in families.items()}
assert ranks == result["ranks"]
receipt = {"schema":"x011-p317-complete-fiber-rank-audit-v1","status":"PASS",
           "curve_order":305,"points":40,"direct_rows":len(saved),"ranks":ranks,
           "result_sha256":hashlib.sha256((H/"result.json").read_bytes()).hexdigest()}
(H/"audit.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
print(json.dumps({"status":"PASS","direct_rows":len(saved),"ranks":ranks},sort_keys=True))
