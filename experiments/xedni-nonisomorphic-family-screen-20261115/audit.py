"""Independent checked-Sage replay of screen and qualified pair family."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
from sage.all import EllipticCurve, GF, QQ

HERE=Path(__file__).resolve().parent
screen=json.loads((HERE/"result.json").read_text())
post=json.loads((HERE/"post-result.json").read_text())
selection=json.loads((HERE.parent/"xedni-large-order-admission-20261115"/"result.json").read_text())
parent=json.loads((HERE.parent/"xedni-fixed-curve-admission-20261115"/"result.json").read_text())

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

selected={r["field_prime"]:r for r in selection["rows"] if r["selected"]}
assert len(selected)==8 and len(screen["rows"])==24
counts=Counter()
curves={}
for row in screen["rows"]:
    p,u=row["field_prime"],row["u"]
    q=row["subgroup_order"]
    assert q==selected[p]["subgroup_order"]
    stdout=HERE/row["stdout_path"];stderr=HERE/row["stderr_path"]
    assert sha(stdout)==row["stdout_sha256"] and sha(stderr)==row["stderr_sha256"]
    assert stderr.read_bytes()==b""
    assert row["exit_code"]==0
    c=json.loads(stdout.read_text().strip().splitlines()[-1])
    assert c==row["candidate"]
    assert c["field_prime"]==p and c["u"]==u
    F=GF(p); E0=EllipticCurve(F,[-1,-2]); P0=E0(2,2)
    m=int(P0.order())//q
    assert m==row["multiplier_m"]==c["multiplier_m"]
    G=m*P0;R=u*G
    assert not R.is_zero() and int(G.order())==q
    x0,y0=map(int,R.xy())
    x=x0 if x0<=p//2 else x0-p
    y=y0 if y0<=p//2 else y0-p
    B=y*y-x*x*x+x
    assert c["reduced_point"]==[x0,y0]
    assert c["centered_point"]==[x,y] and c["curve_B"]==B
    E=EllipticCurve(QQ,[-1,B]);P=E(x,y)
    assert E.discriminant()!=0 and int(E.discriminant())%p!=0
    assert int(E.discriminant())==c["discriminant"]
    assert str(E.j_invariant())==c["j_invariant"]
    assert int(E.torsion_subgroup().order())==c["torsion_order"]
    assert c["torsion_order"]*P!=E(0)
    assert E.change_ring(F).a_invariants()==E0.a_invariants()
    assert E.change_ring(F)(x,y)==R
    curves[p,u]=(E,P)
    counts[row["status"]]+=1
assert dict(counts)==screen["status_counts"]=={"completed":22,"rank_unknown":2}
qualified={(571,3),(677,3)}
assert {(r["field_prime"],r["u"]) for r in screen["rows"]
        if r["u"]>1 and r["candidate"].get("rank_status")=="proved"
        and r["candidate"].get("rank")==1 and r["candidate"].get("torsion_order")==1}==qualified
assert len(post["post_cells"])==2
for cell in post["post_cells"]:
    p,u=cell["field_prime"],cell["u"]
    assert (p,u) in qualified and cell["status"]=="completed"
    stdout=HERE/cell["stdout_path"];stderr=HERE/cell["stderr_path"]
    assert sha(stdout)==cell["stdout_sha256"] and sha(stderr)==cell["stderr_sha256"]
    assert stderr.read_bytes()==b""
    saved=json.loads(stdout.read_text().strip().splitlines()[-1])
    assert saved==cell["result"] and saved["point_is_signed_generator"]
    E,P=curves[p,u]
    assert int(E.rank(proof=True))==1
    gens=list(E.gens(proof=True))
    assert len(gens)==1 and (P==gens[0] or P==-gens[0])
    Ebase=EllipticCurve(QQ,[-1,-2])
    assert E.j_invariant()!=Ebase.j_invariant()
queries=tests=baseline=union=additional=0
for field,old in zip(post["fields"],parent["fields"]):
    p,q=field["field_prime"],field["subgroup_order"]
    assert p==old["field_prime"] and q==old["subgroup_order"]
    F=GF(p);E=EllipticCurve(F,[-1,-2]);P0=E(2,2)
    m=int(P0.order())//q;G=m*P0;Q=17*G
    points=[Q-t*G for t in range(q)]
    images=[{k*P0 for k in range(-4,5)}]
    for pp,u in sorted(qualified):
        if pp==p:
            _,P=curves[pp,u]
            x,y=map(int,P.xy())
            Pmod=E(x,y)
            assert Pmod==u*G
            images.append({k*Pmod for k in range(-4,5)})
    assert field["qualified_models"]==len(images)
    assert field["image_sizes"]==[sum(R in S for R in points) for S in images]
    raw=HERE/field["raw_path"]
    assert sha(raw)==field["raw_sha256"]
    count=base=extra=0
    with gzip.open(raw,"rt") as rows:
        for t1,R1 in enumerate(points):
            for t2,R2 in enumerate(points):
                row=json.loads(next(rows))
                assert row["t"]==[t1,t2]
                mask=sum(1<<j for j,S in enumerate(images) if R1 in S and R2 in S)
                assert row["mask"]==mask
                count+=mask!=0;base+=bool(mask&1);extra+=bool(mask and not(mask&1))
        assert next(rows,None) is None
    assert (field["union_pairs"],field["baseline_pairs"],field["additional_pairs"])==(count,base,extra)
    assert field["pair_tests"]==q*q*len(images)
    assert base==old["admitted_full_pair_support"]
    queries+=q*q;tests+=field["pair_tests"];baseline+=base;union+=count;additional+=extra
assert post["totals"]=={"queries":queries,"pair_tests":tests,"baseline_pairs":baseline,
                        "union_pairs":union,"additional_pairs":additional}
print(json.dumps({"schema":"xedni-nonisomorphic-family-audit-v1","status":"PASS",
                  "screen_rows":24,"rank_proved":22,"rank_unknown":2,
                  "qualified_nonbase_rank_one":2,"queries":queries,"pair_tests":tests,
                  "baseline_pairs":baseline,"union_pairs":union,"additional_pairs":additional},
                 sort_keys=True,indent=2))
