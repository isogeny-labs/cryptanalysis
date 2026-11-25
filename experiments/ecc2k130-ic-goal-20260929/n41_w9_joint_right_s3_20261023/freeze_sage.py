"""Freeze the alternate-association reciprocal controls from exact N41 points."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
SOURCE=ROOT/"n41_n131_w29_rotation_alignment_20261017/aligned_states.json"
PANEL=ROOT/"n41_w9_two_quartic_resultant_20261017/panel.json"
FIXTURE=ROOT/"n41_w9_implicit_fivepair_tower_20261017/fixture.json"
R=PolynomialRing(GF(2),"u")
u=R.gen()
F=GF(2**41,name="u",modulus=u**41+u**3+1)
E=EllipticCurve(F,[1,0,0,0,1])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dec(n):
    n=int(n)
    return F(R([(n>>i)&1 for i in range(41)]))


def enc(x):
    return sum(int(bit)<<i for i,bit in enumerate(x.polynomial().list()))


def s3(a,b,t):
    return (1+(a*b)**2)*t*t+(a*b)*t+a*a+b*b


source=json.loads(SOURCE.read_text())
panel=json.loads(PANEL.read_text())
fixture=json.loads(FIXTURE.read_text())
assert not (HERE/"join_rows.json").exists()
states=[[E(dec(r["point"][0]),dec(r["point"][1])) for r in slot]
        for slot in source["states"]]
target=E(dec(fixture["public_point"][0]),dec(fixture["public_point"][1]))
t=1/target[0]
assert enc(t)==fixture["public_reciprocal"]
rows=[]
for row in panel:
    ids=row["state_ids"]
    P=[states[i][ids[i]] for i in range(5)]
    right=P[3]+P[4]
    left3=P[0]+P[1]+P[2]
    first4=left3+P[3]
    assert all(x!=E(0) and x[0] for x in (right,left3,first4,P[3],P[4]))
    a,b,y=1/P[3][0],1/P[4][0],1/right[0]
    z,w=1/left3[0],1/first4[0]
    assert enc(z)==row["z"]
    assert s3(a,b,y)==0
    preceding_link=s3(z,a,dec(row["w"]))==0
    target_link=s3(z,y,t)==0
    full_relation=sum(P,E(0))==target
    if row["kind"]=="positive":
        assert enc(w)==row["w"] and preceding_link and target_link and full_relation
    else:
        assert not full_relation
    rows.append({"kind":row["kind"],"state_ids":ids,
                 "pair3_reciprocal":enc(a),"pair4_reciprocal":enc(b),
                 "right_sum_reciprocal":enc(y),
                 "actual_first4_reciprocal":enc(w),
                 "preceding_link_zero":preceding_link,
                 "target_link_zero":target_link,
                 "full_relation":full_relation})
out={"status":"FROZEN_EXACT_ALTERNATE_ASSOCIATION_CONTROLS",
     "candidate_id":None,"curve_id":source["curve_id"],
     "source_sha256":sha(SOURCE),"panel_sha256":sha(PANEL),
     "fixture_sha256":sha(FIXTURE),"script_sha256":sha(Path(__file__)),
     "runtime_info_sha256":sha(HERE/"sage_runtime_info.json"),
     "public_reciprocal":enc(t),"rows":rows,
     "positive_count":sum(r["full_relation"] for r in rows),
     "target_link_zero_count":sum(r["target_link_zero"] for r in rows)}
with (HERE/"join_rows.json").open("x") as f:
    json.dump(out,f,sort_keys=True,indent=2)
    f.write("\n")
print(json.dumps({"status":out["status"],"rows":len(rows),
                  "positive_count":out["positive_count"],
                  "target_link_zero_count":out["target_link_zero_count"]}))
