"""Independent N131 W29 group and source audit for the oracle panel."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent/"n41_n131_fivepair_w9_w29_20261017/n131_control.json"
R = PolynomialRing(GF(2), "v")
v = R.gen()
F = GF(2**131,name="v",modulus=v**131+v**13+v**2+v+1)
E = EllipticCurve(F,[1,0,0,0,1])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dec(n):
    n=int(n)
    return F(R([(n>>i)&1 for i in range(131)]))


def enc(x):
    return sum(int(bit)<<i for i,bit in enumerate(x.polynomial().list()))


def halftrace(x):
    ans=F.zero()
    for _ in range(66):
        ans+=x
        x=x**4
    return ans


def point(mask):
    w=dec(mask<<1)
    assert w and not w.trace() and not (1/w).trace()
    h=halftrace(w)
    assert h*h+h==w and h
    return E.lift_x(1+1/h,all=True)[0]


protocol=json.loads((HERE/"protocol.json").read_text())
result=json.loads((HERE/"result.json").read_text())
source=json.loads(SOURCE.read_text())
assert sha(SOURCE)==protocol["source_sha256"]
assert result["protocol_sha256"]==sha(HERE/"protocol.json")
assert not (HERE/"audit_result.json").exists()
assert len(protocol["left_masks"])==128 and len(result["rows"])==256

start=time.monotonic()
seed=protocol["right_positive_mask"] ^ source["pairs"][1]["masks"][1]
assert seed==898618
orbit_distinct=0
for mask in protocol["left_masks"]:
    assert mask and mask < (1<<29) and not (mask & (1<<19))
    a=dec(mask<<1)
    b=dec((mask^seed)<<1)
    assert a and b and not a.trace() and not b.trace()
    assert not (1/a).trace() and not (1/b).trace()
    x=a
    same=False
    for _ in range(131):
        if x==b:
            same=True
            break
        x=x*x
    assert not same
    orbit_distinct+=1

pair_root_sets=[]
for mask in protocol["left_masks"]:
    A=point(mask)
    B=point(mask^seed)
    sums=(A+B,A-B)
    assert all(P!=E(0) and P[0] for P in sums)
    pair_root_sets.append(sorted(enc(1/P[0]) for P in sums))
for i, expected in enumerate(pair_root_sets):
    observed=sorted(result["rows"][2*i+j]["left_root"] for j in range(2))
    assert expected==observed,(i,expected,observed)

left_mask=protocol["left_masks"][0]
right_mask=protocol["right_positive_mask"]
left=point(left_mask)+point(left_mask^seed)
right=point(right_mask)+point(right_mask^seed)
right=E(right[0]**(1<<18),right[1]**(1<<18))
target=left+right
assert enc(1/left[0])==protocol["left_positive_reciprocal"]
assert enc(1/right[0])==protocol["right_positive_reciprocal"]
assert enc(1/target[0])==protocol["target_reciprocal"]
assert result["positive_left_mask"]==left_mask
assert result["positive_right_mask"]==right_mask
positive=[row for row in result["rows"] if row["left_mask"]==left_mask
          and row["left_root"]==protocol["left_positive_reciprocal"]]
assert len(positive)==1
assert {"mask":right_mask,"root":protocol["right_positive_reciprocal"]} in positive[0]["valid_source_candidates"]
elapsed=time.monotonic()-start
audit={"status":"PASS_INDEPENDENT_N131_GROUP_AND_SOURCE_AUDIT",
       "candidate_id":None,"protocol_sha256":sha(HERE/"protocol.json"),
       "producer_sha256":sha(HERE/"result.json"),
       "auditor_sha256":sha(Path(__file__)),
       "source_valid_orbit_distinct_masks":orbit_distinct,
       "pair_root_sets_checked":len(pair_root_sets),
       "positive_group_sum_point":[enc(target[0]),enc(target[1])],
       "positive_target_reciprocal":enc(1/target[0]),
       "audit_seconds":elapsed,
       "self_maxrss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
with (HERE/"audit_result.json").open("x") as out:
    json.dump(audit,out,sort_keys=True,indent=2)
    out.write("\n")
print(json.dumps({k:audit[k] for k in ("status","source_valid_orbit_distinct_masks","pair_root_sets_checked","audit_seconds")}))
