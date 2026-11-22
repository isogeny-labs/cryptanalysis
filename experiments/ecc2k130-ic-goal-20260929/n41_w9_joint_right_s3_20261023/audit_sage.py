"""Independent curve-group replay of the alternate S3 association panel."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
SOURCE=ROOT/"n41_n131_w29_rotation_alignment_20261017/aligned_states.json"
PANEL=ROOT/"n41_w9_two_quartic_resultant_20261017/panel.json"
FIXTURE=ROOT/"n41_w9_implicit_fivepair_tower_20261017/fixture.json"
R=PolynomialRing(GF(2),"v")
v=R.gen()
F=GF(2**41,name="v",modulus=v**41+v**3+1)
E=EllipticCurve(F,[1,0,0,0,1])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dec(n):
    n=int(n)
    return F(R([(n>>i)&1 for i in range(41)]))


def enc(x):
    return sum(int(c)<<i for i,c in enumerate(x.polynomial().list()))


def equation(a,b,c):
    return (1+a*a*b*b)*c*c+(a*b)*c+a*a+b*b


source=json.loads(SOURCE.read_text())
panel=json.loads(PANEL.read_text())
fixture=json.loads(FIXTURE.read_text())
frozen=json.loads((HERE/"join_rows.json").read_text())
build=json.loads((HERE/"build_result.json").read_text())
compact=json.loads((HERE/"compact_build_result.json").read_text())
assert frozen["source_sha256"]==sha(SOURCE)
assert frozen["panel_sha256"]==sha(PANEL)
assert frozen["fixture_sha256"]==sha(FIXTURE)
assert len(panel)==len(frozen["rows"])==33
assert not (HERE/"audit_result.json").exists()
states=[[E(dec(row["point"][0]),dec(row["point"][1])) for row in slot]
        for slot in source["states"]]
target=E(dec(fixture["public_point"][0]),dec(fixture["public_point"][1]))
t=1/target[0]
start=time.monotonic()
rows=[]
for idx,(row,control) in enumerate(zip(panel,frozen["rows"])):
    ids=row["state_ids"]
    assert ids==control["state_ids"]
    points=[states[i][ids[i]] for i in range(5)]
    cols=[column for i,sid in enumerate(ids)
          for column in source["states"][i][sid]["columns"]]
    assert len(cols)==len(set(cols))==10
    L=points[0]+points[1]+points[2]
    D,Epoint=points[3],points[4]
    right=D+Epoint
    first4=L+D
    assert all(P and P[0] for P in (L,D,Epoint,right,first4))
    z,u,vcoord,y=1/L[0],1/D[0],1/Epoint[0],1/right[0]
    assert [enc(z),enc(u),enc(vcoord),enc(y)]==[
        row["z"],control["pair3_reciprocal"],
        control["pair4_reciprocal"],control["right_sum_reciprocal"]]
    assert equation(u,vcoord,y)==0
    first4_gate=equation(z,u,dec(row["w"]))==0
    target_gate=equation(z,y,t)==0
    complete=L+right==target
    assert first4_gate==control["preceding_link_zero"]
    assert target_gate==control["target_link_zero"]
    assert complete==control["full_relation"]
    for circuit in (build,compact):
        check=circuit["controls_checked"][idx]
        assert check["kind"]==row["kind"]
        assert check["pair3_zero"] and check["right_sum_zero"]
        assert check["preceding_s3_zero"]==first4_gate
        assert check["joint_target_zero"]==target_gate
    rows.append({"index":idx,"kind":row["kind"],
                 "complete":complete,"target_gate":target_gate,
                 "preceding_gate":first4_gate})
assert rows[0]["complete"] and rows[0]["target_gate"]
assert all(not r["complete"] and not r["target_gate"] for r in rows[1:])
result={"status":"PASS_INDEPENDENT_GROUP_JOINT_S3_AUDIT",
        "candidate_id":None,"source_sha256":sha(SOURCE),
        "panel_sha256":sha(PANEL),"fixture_sha256":sha(FIXTURE),
        "join_rows_sha256":sha(HERE/"join_rows.json"),
        "build_result_sha256":sha(HERE/"build_result.json"),
        "compact_build_result_sha256":sha(HERE/"compact_build_result.json"),
        "auditor_sha256":sha(Path(__file__)),
        "checked_rows":len(rows),
        "complete_relation_rows":sum(r["complete"] for r in rows),
        "target_gate_zero_rows":sum(r["target_gate"] for r in rows),
        "audit_seconds":time.monotonic()-start,
        "self_maxrss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "rows":rows}
with (HERE/"audit_result.json").open("x") as out:
    json.dump(result,out,sort_keys=True,indent=2)
    out.write("\n")
print(json.dumps({k:result[k] for k in ("status","checked_rows","complete_relation_rows","target_gate_zero_rows")}))
