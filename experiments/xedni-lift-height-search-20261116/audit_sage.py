"""Independent Sage replay of all candidate curves, scores, and winners."""
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
protocol=json.loads((HERE/"protocol.json").read_text())
result=json.loads((HERE/"result.json").read_text())
source=ROOT/"xedni-common-preimage-lift-20261116"/"lifts.jsonl"
assert hashlib.sha256(source.read_bytes()).hexdigest()==protocol["source_lifts_sha256"]
for name,key in (("rows.jsonl","rows_sha256"),("winners.jsonl","winners_sha256")):
    assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==result[key]
events=[json.loads(line) for line in source.open()]
rows=[json.loads(line) for line in (HERE/"rows.jsonl").open()]
winners=[json.loads(line) for line in (HERE/"winners.jsonl").open()]
assert len(events)==len(winners)==159 and len(rows)==159*27


def coordinate_bits(z):
    return max(abs(int(z.numerator())).bit_length(),int(z.denominator()).bit_length())


counts=Counter()
for i,event in enumerate(events):
    p=event["field_prime"]
    a,b=event["vector"]
    x0,y0=event["T"]
    finite=EllipticCurve(GF(p),[-1,-2])
    S=finite(*event["S"])
    U,V=finite(*event["U"]),finite(*event["V"])
    assert b*S==U and bool((-a)*S==V)==event["public_relation"]
    best=None
    for j,(kx,ky,kA) in enumerate(itertools.product((-1,0,1),repeat=3)):
        row=rows[i*27+j]
        assert row["event_index"]==i and row["shift"]==[kx,ky,kA]
        x,y=x0+kx*p,y0+ky*p
        A=-1+kA*p
        B=y*y-x*x*x-A*x
        assert row["T"]==[x,y] and row["A"]==A and row["B"]==B
        curve=EllipticCurve(QQ,[A,B])
        assert int(curve.discriminant())%p!=0
        T=curve(x,y)
        P,R=b*T,-a*T
        assert (a*P+b*R).is_zero()
        assert row["P"]==[str(P[0]),str(P[1])]
        assert row["R"]==[str(R[0]),str(R[1])]
        rP=finite(GF(p)(P[0]),GF(p)(P[1]))
        rR=finite(GF(p)(R[0]),GF(p)(R[1]))
        assert [int(rP[0]),int(rP[1])]==row["P_reduction"]==event["U"]
        assert [int(rR[0]),int(rR[1])]==row["R_reduction"]
        assert bool(rR==V)==event["public_relation"]
        score=max(coordinate_bits(z) for z in (P[0],P[1],R[0],R[1]))
        assert row["score_bits"]==score and row["status"]=="pass"
        key=(score,kx,ky,kA)
        if best is None or key<best[0]:
            best=(key,row)
        counts["candidate_pass"]+=1
    winner=winners[i]
    assert winner["shift"]==best[1]["shift"] and winner["score_bits"]==best[0][0]
    baseline=rows[i*27+13]
    assert baseline["shift"]==[0,0,0]
    assert winner["baseline_score_bits"]==baseline["score_bits"]
    assert winner["improvement_bits"]==baseline["score_bits"]-winner["score_bits"]
    counts["winner_pass"]+=1
    counts["improved_events"]+=int(winner["improvement_bits"]>0)

assert counts["candidate_pass"]==4293 and counts["winner_pass"]==159
assert counts["improved_events"]==result["counts"]["improved_events"]
receipt={"schema":"xedni-lift-height-search-sage-audit-v1","status":"PASS",
         "counts":dict(sorted(counts.items())),"rows_sha256":result["rows_sha256"],
         "winners_sha256":result["winners_sha256"]}
(HERE/"audit-sage.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
