"""Degree-two Hecke rank and signed direct controls on a frozen X011 fiber."""
from collections import Counter
from pathlib import Path
from sage.all import GF, QQ, classical_modular_polynomial, matrix
import gzip
import hashlib
import importlib.util
import itertools
import json
import os
import time

H = Path(__file__).resolve().parent
P = json.loads((H/"protocol.json").read_text())
started = time.monotonic()
p = P["p"]
archive = Path(os.environ.get("ARCHIVE_ROOT","/Volumes/SSD990/cryptanalysis"))
source_path = archive/"experiments/hecke-d1407-f6-20261023/regularized/tools/hecke11.py"
assert hashlib.sha256(source_path.read_bytes()).hexdigest() == P["regularized_hecke_source_sha256"]
spec = importlib.util.spec_from_file_location("hecke11_p1009_rank",source_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
build_started=time.monotonic()
funcs,jfun=mod.build([2])
build_seconds=time.monotonic()-build_started
R=mod.Reduced(p,funcs,jfun,[2])
E=R.E
assert int(E.cardinality()) == P["curve_order"]
ledger_blob=(H/P["corrected_ledger"]).resolve().read_bytes()
assert hashlib.sha256(ledger_blob).hexdigest() == P["corrected_ledger_sha256"]
fiber=sorted((r for r in (json.loads(s) for s in gzip.decompress(ledger_blob).splitlines())
              if r["p"]==p and r["status"]=="regular" and r["abs_trace"]==P["fiber_abs_trace"]),
             key=lambda r:(r["x"],r["y"]))
assert len(fiber) == P["expected_fiber_size"]
points=[E(r["x"],r["y"]) for r in fiber]
index={Q:i for i,Q in enumerate(points)}
assert len(index)==len(points)
for r,Q in zip(fiber,points):
    assert R.j(Q)==R.Fp(r["j"])


def rank(rows,ring):
    return int(matrix(ring,[[r.get(i,0) for i in range(len(points))] for r in rows]).rank())


def verify(row):
    assert sum((c*points[i] for i,c in row.items()),E(0))==E(0)


phi=classical_modular_polynomial(2)
statuses=Counter()
source_records=[]
hecke=[]
hecke_start=time.monotonic()
for i,Q in enumerate(points):
    poly=R.neighbour_x(2,Q)
    factors=[[int(f.degree()),int(n)] for f,n in poly.factor()]
    entry={"source":i,"point":[int(Q[0]),int(Q[1])],"factor_pattern":factors}
    nb=R.neighbours_all(2,Q)
    if nb is None:
        entry["status"]="NO_UNIQUE_COMPLETE_RATIONAL_FIBER"
    else:
        assert len(nb)==3 and sum(nb,E(0))==R.a_l[2]*Q
        jQ=R.j(Q)
        js=[R.j(T) for T in nb]
        if any(j is None for j in js):
            entry["status"]="CUSP_NEIGHBOR"
        else:
            assert all(phi(jQ,jT)==0 for jT in js)
            if any(T not in index for T in nb):
                entry["status"]="OUTSIDE_FROZEN_FIBER"
            else:
                row=Counter(index[T] for T in nb)
                row[i]-=R.a_l[2]
                row={j:int(c) for j,c in row.items() if c}
                verify(row)
                entry["status"]="CLASS_CLOSED"
                entry["row"]={str(j):c for j,c in sorted(row.items())}
                hecke.append(row)
    statuses[entry["status"]]+=1
    source_records.append(entry)
    assert time.monotonic()-started < P["resource_cap_seconds"]
hecke_seconds=time.monotonic()-hecke_start


def neg(A):
    return None if A is None else (A[0],(-A[1]-1)%p)


def add(A,B):
    if A is None:return B
    if B is None:return A
    x,y=A;u,v=B
    if x==u and (y+v+1)%p==0:return None
    if A==B:top,bottom=3*x*x-2*x-10,2*y+1
    else:top,bottom=v-y,u-x
    slope=top*pow(bottom%p,-1,p)%p
    intercept=(y-slope*x)%p
    X=(slope*slope+1-x-u)%p
    Y=(-slope*X-intercept-1)%p
    assert (Y*Y+Y-X*X*X+X*X+10*X+20)%p==0
    return (X,Y)


coords=[(int(Q[0]),int(Q[1])) for Q in points]
direct=[]
direct_counts=Counter()
direct_start=time.monotonic()
for support in range(1,4):
    for inds in itertools.combinations(range(len(points)),support):
        for tail in itertools.product((-1,1),repeat=support-1):
            signs=(1,)+tail
            total=None
            for k,sgn in zip(inds,signs):
                total=add(total,coords[k] if sgn==1 else neg(coords[k]))
            if total is not None:continue
            row=dict(zip(inds,signs))
            verify(row)
            direct.append({"indices":list(inds),"coefficients":list(signs)})
            direct_counts[support]+=1
    assert time.monotonic()-started < P["resource_cap_seconds"]
direct_seconds=time.monotonic()-direct_start
direct_rows=[dict(zip(r["indices"],r["coefficients"])) for r in direct]
rank_start=time.monotonic()
ranks={"hecke_only":{"QQ":rank(hecke,QQ),"F17":rank(hecke,GF(17))},
       "direct_only":{"QQ":rank(direct_rows,QQ),"F17":rank(direct_rows,GF(17))},
       "hecke_plus_direct":{"QQ":rank(hecke+direct_rows,QQ),"F17":rank(hecke+direct_rows,GF(17))}}
rank_seconds=time.monotonic()-rank_start
raw=b"".join(json.dumps(r,sort_keys=True,separators=(",", ":")).encode()+b"\n" for r in direct)
packed=gzip.compress(raw,compresslevel=9,mtime=0)
(H/"direct-rows.jsonl.gz").write_bytes(packed)
out={"schema":"x011-p1009-degree2-rank-result-v1","status":"complete",
     "protocol_sha256":hashlib.sha256((H/"protocol.json").read_bytes()).hexdigest(),
     "p":p,"fiber_size":len(points),"source_records":source_records,
     "hecke_statuses":dict(statuses),"hecke_rows":len(hecke),
     "direct_candidate_counts":{str(k):direct_counts[k] for k in range(1,4)},
     "direct_rows_sha256":hashlib.sha256(raw).hexdigest(),
     "direct_rows_gzip_sha256":hashlib.sha256(packed).hexdigest(),
     "ranks":ranks,
     "stage_seconds":{"function_build":round(build_seconds,3),"hecke_rows":round(hecke_seconds,3),
                      "direct_enumeration":round(direct_seconds,3),"matrix_ranks":round(rank_seconds,3)},
     "candidate_id":None,"target_online_ms":None}
(H/"result.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
print(json.dumps({"hecke_statuses":dict(statuses),"direct_candidate_counts":out["direct_candidate_counts"],"ranks":ranks},sort_keys=True))
