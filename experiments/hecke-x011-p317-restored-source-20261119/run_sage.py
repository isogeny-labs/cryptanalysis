"""Reconstruct exact Hecke fibers from frozen source moments at (16,60)."""
from collections import Counter
from pathlib import Path
from sage.all import EllipticCurve, GF, QQ, PolynomialRing, classical_modular_polynomial, matrix, vector
import hashlib
import json
import math
import time

H = Path(__file__).resolve().parent
P = json.loads((H/"protocol.json").read_text())
PRE = json.loads((H/"pre-run.json").read_text())
start = time.monotonic()


def load(path,digest):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest
    return json.loads(raw)


M = load(H/"moments.json",PRE["moments_sha256"])["moments"]
outside_archive = load(H/"archived-outside.json",PRE["archived_outside_sha256"])["rows"]
parent = H.parent/"hecke-x011-p317-complete-fiber-rank-20261119"
parent_result = load(parent/"result.json",P["class_rank_result_sha256"])
archived = load(parent/"archived-inputs.json",P["archived_inputs_sha256"])
assert parent_result["points"] == 40
p = P["p"]
Fp = GF(p)
E = EllipticCurve(Fp,[0,-1,1,-10,-20])
source = E(16,60)
points = [E(x,y) for x,y in archived["class_points"]] + [source]
index = {Q:i for i,Q in enumerate(points)}
assert len(index) == 40 and index[source] == 39
jtable = json.loads((H.parent/"hecke-x011-trace-fiber-census-20261119/jfun.json").read_text())


def j_value(Q):
    if Q.is_zero():
        return None
    F = Q.base_ring()
    if Q[0] == F(16):
        return F(-121) if Q[1] == F(60) else None
    numer = sum(F(n)/F(d)*Q[0]**a*Q[1]**b for a,b,(n,d) in jtable["A_terms"])
    return numer/(Q[0]-F(16))**11


def rank(rows,field):
    return int(matrix(field,[[r.get(i,0) for i in range(40)] for r in rows]).rank())


def raw_row(entry):
    return {int(i):int(c) for i,c in entry.items() if c}


def verify_row(row):
    assert sum((c*points[i] for i,c in row.items()),E(0)) == E(0)


baseline = [raw_row(x) for key in ("base_rows","closed_rows","short_cancellation_rows") for x in archived[key]]
for r in baseline:
    verify_row(r)
assert rank(baseline,QQ) == 39 and rank(baseline,GF(61)) == 38
T = PolynomialRing(Fp,"T").gen()
outputs = []
new_rows = []
for ell in P["degrees"]:
    phase_start = time.monotonic()
    moments = M[str(ell)]
    s = [None]+[Fp(x) for x in moments["x"]]
    elementary = [Fp(1)]+[Fp(0)]*(ell+1)
    for k in range(1,ell+2):
        elementary[k] = sum((-1)**(i-1)*elementary[k-i]*s[i] for i in range(1,k+1))/Fp(k)
    poly = sum((-1)**k*elementary[k]*T**(ell+1-k) for k in range(ell+2))
    pattern = [[int(f.degree()),int(n)] for f,n in poly.factor()]
    degree = math.lcm(*(d for d,_ in pattern))
    entry = {"degree":ell,"a_ell":moments["a_ell"],"factor_pattern":pattern,
             "splitting_degree":degree,"neighbor_x_coefficients":[int(c) for c in poly.list()]}
    if degree > P["degree13_extension_cap"] or any(n != 1 for _,n in pattern):
        entry["status"] = "EXTENSION_OR_REPEAT_CAP"
        outputs.append(entry)
        continue
    F = Fp if degree == 1 else GF(p**degree,name=f"z{degree}")
    EE = E.change_ring(F)
    src = EE(F(16),F(60))
    roots = sorted(poly.change_ring(F).roots(multiplicities=False),key=str)
    assert len(roots) == ell+1
    V = matrix(F,[[x**k for x in roots] for k in range(ell+1)])
    ys = V.solve_right(vector(F,[F(v) for v in moments["xy"]]))
    neighbors = [EE(x,y) for x,y in zip(roots,ys)]
    assert all(sum(Q[1]*Q[0]**k for Q in neighbors) == F(moments["xy"][k]) for k in range(ell+1))
    assert sum(neighbors,EE(0)) == moments["a_ell"]*src
    phi = classical_modular_polynomial(ell)
    modular_checks = Counter()
    for Q in neighbors:
        jq = j_value(Q)
        if jq is None:
            modular_checks["pole"] += 1
        else:
            assert phi(F(-121),jq) == 0
            modular_checks["finite"] += 1
    lifted = [EE(F(Q[0]),F(Q[1])) for Q in points]
    lifted_index = {Q:i for i,Q in enumerate(lifted)}
    unseen = set(neighbors)
    class_row = Counter({39:-moments["a_ell"]})
    outside = []
    orbits = []
    while unseen:
        seed = min(unseen,key=lambda Q:(str(Q[0]),str(Q[1])))
        orbit=[]
        Q=seed
        while Q not in orbit:
            orbit.append(Q)
            Q=EE(Q[0]**p,Q[1]**p)
        assert Q == seed and all(Q in unseen for Q in orbit)
        unseen.difference_update(orbit)
        trace = sum(orbit,EE(0))
        if trace.is_zero():
            status,coord="IDENTITY",None
        elif trace in lifted_index:
            status="IN_CLASS"
            coord=[int(trace[0]),int(trace[1])]
            class_row[lifted_index[trace]] += 1
        else:
            assert trace[0]**p == trace[0] and trace[1]**p == trace[1]
            status="OUTSIDE_CLASS"
            coord=[int(trace[0]),int(trace[1])]
            outside.append(coord)
        orbits.append({"size":len(orbit),"status":status,"trace":coord})
    entry["modpoly_checks"] = dict(modular_checks)
    entry["orbits"] = orbits
    entry["class_part"] = {str(i):c for i,c in sorted(class_row.items()) if c}
    entry["outside_traces"] = sorted(outside)
    if not outside:
        row = dict(class_row)
        row = {i:c for i,c in row.items() if c}
        verify_row(row)
        new_rows.append({"degree":ell,"kind":"CLASS_CLOSED","row":row})
        entry["status"] = "CLASS_CLOSED"
    else:
        matches = [a for a in outside_archive if sorted(a["outside_traces"]) == sorted(outside)]
        entry["status"] = "OUTSIDE_CLASS_TRACE"
        entry["matched_archived_sources"] = [a["source"] for a in matches]
        for a in matches:
            row = Counter(class_row)
            row.subtract(raw_row(a["class_part"]))
            row = {i:c for i,c in row.items() if c}
            verify_row(row)
            new_rows.append({"degree":ell,"kind":"CANCEL_ARCHIVED_OUTSIDE","archived_source":a["source"],"row":row})
    entry["elapsed_wall_seconds"] = round(time.monotonic()-phase_start,3)
    outputs.append(entry)
    assert time.monotonic()-start < P["resource_cap_seconds"]
rows = [raw_row(x["row"]) for x in new_rows]
ranks = {"baseline":{"QQ":rank(baseline,QQ),"F61":rank(baseline,GF(61))},
         "new_only":{"QQ":rank(rows,QQ),"F61":rank(rows,GF(61))},
         "baseline_plus_new":{"QQ":rank(baseline+rows,QQ),"F61":rank(baseline+rows,GF(61))}}
result = {"schema":"x011-p317-restored-source-result-v1","status":"complete",
          "protocol_sha256":hashlib.sha256((H/"protocol.json").read_bytes()).hexdigest(),
          "pre_run_sha256":hashlib.sha256((H/"pre-run.json").read_bytes()).hexdigest(),
          "source_point":[16,60],"fibers":outputs,"new_rows":new_rows,"ranks":ranks,
          "elapsed_wall_seconds":round(time.monotonic()-start,3),
          "candidate_id":None,"target_online_ms":None}
(H/"result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps({"statuses":{str(x["degree"]):x["status"] for x in outputs},"new_rows":len(new_rows),"ranks":ranks},sort_keys=True))
