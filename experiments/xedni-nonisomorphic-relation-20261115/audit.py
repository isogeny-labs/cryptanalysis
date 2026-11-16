"""Independent checked-Sage replay of qualified rational relation census."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
from sage.all import EllipticCurve, GF, QQ

HERE=Path(__file__).resolve().parent
result=json.loads((HERE/"result.json").read_text())
screen=json.loads((HERE.parent/"xedni-nonisomorphic-family-screen-20261115"/"result.json").read_text())
post=json.loads((HERE.parent/"xedni-nonisomorphic-family-screen-20261115"/"post-result.json").read_text())
extra={(r["field_prime"],r["u"]):r["candidate"] for r in screen["rows"]
       if r["u"]>1 and r["candidate"].get("rank_status")=="proved"
       and r["candidate"].get("rank")==1 and r["candidate"].get("torsion_order")==1}
assert set(extra)=={(571,3),(677,3)}
E0Q=EllipticCurve(QQ,[-1,-2]);P0Q=E0Q(2,2)
assert int(E0Q.rank(proof=True))==1 and int(E0Q.torsion_subgroup().order())==1
curves={"base":(E0Q,P0Q)}
for (p,u),c in extra.items():
    E=EllipticCurve(QQ,[-1,c["curve_B"]]);x,y=c["centered_point"];P=E(x,y)
    assert int(E.rank(proof=True))==1 and int(E.torsion_subgroup().order())==1
    gens=list(E.gens(proof=True));assert len(gens)==1 and (P==gens[0] or P==-gens[0])
    assert E.j_invariant()!=E0Q.j_invariant()
    curves[p,"u3"]=(E,P)
queries=membership=relation_tests=public_tests=hits=0
for field,admit in zip(result["fields"],post["fields"]):
    p,q=field["field_prime"],field["subgroup_order"]
    assert p==admit["field_prime"] and q==admit["subgroup_order"]
    F=GF(p);Ebase=EllipticCurve(F,[-1,-2]);Pbase=Ebase(2,2)
    m=int(Pbase.order())//q;G=m*Pbase;Q=17*G
    assert int(G.order())==q
    points=[Q-t*G for t in range(q)]
    models=[]
    for model in field["models"]:
        tag=model["tag"]
        E,P=curves["base"] if tag=="base" else curves[p,tag]
        assert model["curve_B"]==int(E.a6())
        assert E.discriminant()!=0 and int(E.discriminant())%p!=0
        assert E.change_ring(F).a_invariants()==Ebase.a_invariants()
        x,y=map(int,P.xy());Pmod=Ebase(x,y)
        if tag=="base": assert Pmod==Pbase
        else: assert Pmod==model["u"]*G
        coeff={R:k for k in range(-4,5) for R in [k*Pmod]}
        expected={str((17-t)%q):coeff[points[t]] for t in range(q) if points[t] in coeff}
        assert expected==model["reduced_scalar_to_rational_coordinate"]
        models.append((E,P,coeff))
    counters=[Counter() for _ in models]
    positive=[]
    raw=HERE/field["raw_path"]
    assert hashlib.sha256(raw.read_bytes()).hexdigest()==field["raw_sha256"]
    with gzip.open(raw,"rt") as rows:
        for t1,R1 in enumerate(points):
            for t2,R2 in enumerate(points):
                row=json.loads(next(rows))
                assert row["t"]==[t1,t2] and len(row["status"])==len(models)
                for j,(E,P,coeff) in enumerate(models):
                    if R1.is_zero() or R2.is_zero(): status="identity"
                    elif R1==R2: status="duplicate"
                    elif R1 not in coeff or R2 not in coeff: status="outside_cap"
                    else:
                        k1,k2=coeff[R1],coeff[R2]
                        U,V=k1*P,k2*P
                        rational=(U+2*V).is_zero()
                        public=(R1+2*R2).is_zero()
                        assert rational==public==(k1+2*k2==0)
                        relation_tests+=1;public_tests+=1
                        counters[j]["rational_relation_tests"]+=1
                        counters[j]["public_relation_tests"]+=1
                        if rational:
                            status="rational_relation"
                            recovered=((t1+2*t2)*pow(3,-1,q))%q
                            assert recovered==17 and recovered*G==Q
                            positive.append({"field_prime":p,"model":field["models"][j]["tag"],
                                             "t":[t1,t2],"k":[k1,k2],
                                             "public_scalars":[(17-t1)%q,(17-t2)%q],
                                             "curve_B":int(E.a6()),"recovered_scalar":recovered,
                                             "query_index_one_based":t1*q+t2+1})
                        else: status="admitted_nonrelation"
                    assert row["status"][j]==status
                    counters[j][status]+=1
                membership+=len(models)
        assert next(rows,None) is None
    assert positive==field["relation_hits"]
    assert field["first_relation"]==(positive[0] if positive else None)
    for model,count in zip(field["models"],counters):assert model["counts"]==dict(count)
    assert field["candidate_pair_membership_tests"]==q*q*len(models)
    queries+=q*q;hits+=len(positive)
assert result["totals"]=={"queries":queries,"candidate_pair_membership_tests":membership,
                         "rational_relation_tests":relation_tests,"public_relation_tests":public_tests,
                         "rational_relations":hits,"rank_screen_candidates":24,
                         "rank_exact_unknown":2,"generator_proof_cells":2}
print(json.dumps({"schema":"xedni-nonisomorphic-relation-audit-v1","status":"PASS",
                  "fields":8,"queries":queries,"membership_tests":membership,
                  "rational_relation_tests":relation_tests,"public_relation_tests":public_tests,
                  "rational_relations":hits,"scalar_replays":hits},sort_keys=True,indent=2))
