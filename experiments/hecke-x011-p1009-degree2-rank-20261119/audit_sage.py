"""Independent Sage replay of the p1009 factorization and direct controls."""
from collections import Counter
from pathlib import Path
from sage.all import GF, QQ, matrix
import gzip
import hashlib
import importlib.util
import itertools
import json
import os

H=Path(__file__).resolve().parent
protocol=json.loads((H/"protocol.json").read_text())
post=json.loads((H/"post-run.json").read_text())
raw=(H/"result.json").read_bytes()
assert hashlib.sha256(raw).hexdigest()==post["producer_result_sha256"]
result=json.loads(raw)
archive=Path(os.environ.get("ARCHIVE_ROOT","/Volumes/SSD990/cryptanalysis"))
source=archive/"experiments/hecke-d1407-f6-20261023/regularized/tools/hecke11.py"
assert hashlib.sha256(source.read_bytes()).hexdigest()==protocol["regularized_hecke_source_sha256"]
spec=importlib.util.spec_from_file_location("hecke11_p1009_audit",source)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
funcs,jfun=mod.build([2])
R=mod.Reduced(1009,funcs,jfun,[2])
E=R.E
assert int(E.cardinality())==1020
ledger=(H/protocol["corrected_ledger"]).resolve().read_bytes()
assert hashlib.sha256(ledger).hexdigest()==protocol["corrected_ledger_sha256"]
fiber=sorted((r for r in (json.loads(s) for s in gzip.decompress(ledger).splitlines())
              if r["p"]==1009 and r["status"]=="regular" and r["abs_trace"]==20),
             key=lambda r:(r["x"],r["y"]))
points=[E(r["x"],r["y"]) for r in fiber]
assert len(points)==84
patterns=Counter()
polynomial_certificates=[]
for i,(Q,saved) in enumerate(zip(points,result["source_records"])):
    assert R.j(Q)==R.Fp(fiber[i]["j"])
    assert saved["source"]==i and saved["point"]==[int(Q[0]),int(Q[1])]
    poly=R.neighbour_x(2,Q)
    pattern=[[int(f.degree()),int(m)] for f,m in poly.factor()]
    assert pattern==saved["factor_pattern"]==[[1,1],[2,1]]
    assert len(poly.roots())==1
    root=int(poly.roots()[0][0])
    quad=next(f for f,m in poly.factor() if f.degree()==2)
    coeff=[int(c) for c in quad.list()]
    disc=(coeff[1]*coeff[1]-4*coeff[0]*coeff[2])%1009
    assert all((y*y)%1009!=disc for y in range(1009))
    polynomial_certificates.append({"source":i,"cubic":[int(c) for c in poly.list()],
                                    "linear_root":root,"quadratic":coeff,"discriminant":disc})
    assert R.neighbours_all(2,Q) is None
    assert saved["status"]=="NO_UNIQUE_COMPLETE_RATIONAL_FIBER"
    patterns[str(pattern)]+=1
assert patterns=={"[[1, 1], [2, 1]]":84}
saved_rows=[json.loads(s) for s in gzip.open(H/"direct-rows.jsonl.gz","rt")]
replayed=[]
for support in range(1,4):
    for inds in itertools.combinations(range(84),support):
        for tail in itertools.product((-1,1),repeat=support-1):
            signs=(1,)+tail
            if sum((signs[k]*points[i] for k,i in enumerate(inds)),E(0))==E(0):
                replayed.append({"indices":list(inds),"coefficients":list(signs)})
assert replayed==saved_rows
counts=Counter(len(r["indices"]) for r in replayed)
assert {str(k):counts[k] for k in range(1,4)}==result["direct_candidate_counts"]
def rank(rows,ring):
    M=matrix(ring,[[dict(zip(r["indices"],r["coefficients"])).get(i,0) for i in range(84)] for r in rows])
    return int(M.rank())
ranks={"QQ":rank(replayed,QQ),"F17":rank(replayed,GF(17))}
assert ranks==result["ranks"]["direct_only"]==result["ranks"]["hecke_plus_direct"]
assert result["ranks"]["hecke_only"]=={"QQ":0,"F17":0}
certificate_bytes=(json.dumps(polynomial_certificates,sort_keys=True,separators=(",",":"))+"\n").encode()
(H/"polynomial-certificates.json").write_bytes(certificate_bytes)
audit={"schema":"x011-p1009-degree2-rank-audit-v1","status":"PASS",
       "factor_patterns":dict(patterns),"direct_rows":len(replayed),"direct_counts":result["direct_candidate_counts"],
       "ranks":ranks,"result_sha256":post["producer_result_sha256"],
       "polynomial_certificates_sha256":hashlib.sha256(certificate_bytes).hexdigest()}
(H/"audit.json").write_text(json.dumps(audit,sort_keys=True,indent=2)+"\n")
print(json.dumps({"status":"PASS","factor_patterns":dict(patterns),"direct_rows":len(replayed),"ranks":ranks},sort_keys=True))
