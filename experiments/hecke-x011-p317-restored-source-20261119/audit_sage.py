"""Fresh function build and independent neighbor-orbit replay."""
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing, matrix, vector
import hashlib
import importlib.util
import json
import math
import os

H = Path(__file__).resolve().parent
protocol = json.loads((H/"protocol.json").read_text())
saved = json.loads((H/"result.json").read_text())
frozen = json.loads((H/"moments.json").read_text())["moments"]
archive = Path(os.environ.get("ARCHIVE_ROOT","/Volumes/SSD990/cryptanalysis"))
source_path = archive/"experiments/hecke-d1407-f6-20261023/regularized/tools/hecke11.py"
assert hashlib.sha256(source_path.read_bytes()).hexdigest() == protocol["regularized_hecke_source_sha256"]
spec = importlib.util.spec_from_file_location("hecke11_restored_source_audit",source_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
funcs,jfun = mod.build([2,5,13])
R = mod.Reduced(317,funcs,jfun,[2,5,13])
P = R.E(16,60)
assert R.j(P) == R.Fp(-121)
parent = H.parent/"hecke-x011-p317-complete-fiber-rank-20261119"
pts = json.loads((parent/"archived-inputs.json").read_text())["class_points"]+[[16,60]]
class_points = [R.E(x,y) for x,y in pts]
point_set = {Q:i for i,Q in enumerate(class_points)}
assert len(point_set) == 40 and point_set[P] == 39
replayed=[]
for ell in [2,5,13]:
    assert int(mod.E0.ap(ell)) == frozen[str(ell)]["a_ell"]
    assert [int(R.funcs[(ell,"x",k)](P[0],P[1])) for k in range(1,ell+2)] == frozen[str(ell)]["x"]
    assert [int(R.funcs[(ell,"xy",k)](P[0],P[1])) for k in range(ell+1)] == frozen[str(ell)]["xy"]
    poly = R.neighbour_x(ell,P)
    pattern = [[int(f.degree()),int(n)] for f,n in poly.factor()]
    stored = next(x for x in saved["fibers"] if x["degree"] == ell)
    assert pattern == stored["factor_pattern"]
    assert [int(c) for c in poly.list()] == stored["neighbor_x_coefficients"]
    d = math.lcm(*(a for a,_ in pattern))
    F = GF(317) if d == 1 else GF(317**d,name=f"audit{d}")
    E = R.E.change_ring(F)
    roots = sorted(poly.change_ring(F).roots(multiplicities=False),key=str)
    assert len(roots) == ell+1
    mixed = matrix(F,[[x**k for x in roots] for k in range(ell+1)])
    ys = mixed.solve_right(vector(F,[R.funcs[(ell,"xy",k)](P[0],P[1]) for k in range(ell+1)]))
    neighbors = [E(x,y) for x,y in zip(roots,ys)]
    assert sum(neighbors,E(0)) == R.a_l[ell]*E(F(16),F(60))
    if ell == 2:
        from_api = R.neighbours_all(2,P)
        assert sorted((int(Q[0]),int(Q[1])) for Q in from_api) == sorted((int(Q[0]),int(Q[1])) for Q in neighbors)
    remaining=set(neighbors)
    inside=[]
    outside=[]
    orbits=[]
    embedded={E(F(Q[0]),F(Q[1])):i for i,Q in enumerate(class_points)}
    while remaining:
        seed=min(remaining,key=lambda Q:(str(Q[0]),str(Q[1])))
        orbit=[]
        Q=seed
        while Q not in orbit:
            orbit.append(Q)
            Q=E(Q[0]**317,Q[1]**317)
        assert Q==seed
        remaining.difference_update(orbit)
        trace=sum(orbit,E(0))
        if trace.is_zero():
            status,coord="IDENTITY",None
        elif trace in embedded:
            status="IN_CLASS"
            coord=[int(trace[0]),int(trace[1])]
            inside.append(embedded[trace])
        else:
            status="OUTSIDE_CLASS"
            coord=[int(trace[0]),int(trace[1])]
            outside.append(coord)
        orbits.append({"size":len(orbit),"status":status,"trace":coord})
    assert orbits == stored["orbits"]
    assert sorted(outside) == stored["outside_traces"]
    counts={39:-R.a_l[ell]}
    for i in inside:
        counts[i]=counts.get(i,0)+1
    assert {str(i):c for i,c in sorted(counts.items()) if c} == stored["class_part"]
    replayed.append({"degree":ell,"factor_pattern":pattern,"outside_traces":sorted(outside)})
assert saved["new_rows"] == [{"degree":2,"kind":"CLASS_CLOSED","row":{"15":1,"17":1,"36":1,"39":2}}]
receipt={"schema":"x011-p317-restored-source-audit-v1","status":"PASS",
         "fresh_build_degrees":[2,5,13],"replayed":replayed,
         "result_sha256":hashlib.sha256((H/"result.json").read_bytes()).hexdigest()}
(H/"audit.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
print(json.dumps({"status":"PASS","replayed_degrees":[2,5,13]},sort_keys=True))
