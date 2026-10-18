"""Audit the two-quadratic final-pair root map for every N41 source state."""
import hashlib
import json
import resource
import signal
import time
from collections import defaultdict
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE=Path(__file__).resolve().parent
protocol=json.loads((HERE/"audit_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path,digest in protocol["sources"].items():
    assert sha(path)==digest,path
assert not (HERE/"audit_result.json").exists()
signal.signal(signal.SIGALRM,lambda _s,_f: (_ for _ in ()).throw(TimeoutError("two-quadratic audit cap")))
signal.alarm(protocol["wall_cap_seconds"])
started=time.monotonic()
source=json.loads(Path(protocol["states"]).read_text())
fixture=json.loads(Path(protocol["fixture"]).read_text())
table=json.loads(Path(protocol["w_table"]).read_text())
prior=json.loads(Path(protocol["w_audit"]).read_text())
assert prior["status"]=="PASS_ALL_CODE_QUARTIC_ROOTS_EQUAL_TARGET_TABLE"
assert source["curve_id"]==protocol["curve_id"] and source["rotations"][4]==24

K=PolynomialRing(GF(2),"u")
u=K.gen()
F=GF(2**41,name="u",modulus=u**41+u**3+1)
R=PolynomialRing(F,"Z")
Z=R.gen()


def dec(value):
    return F(K([(int(value)>>i)&1 for i in range(41)]))


def enc(value):
    return sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))


bits=[i for i in range(9) if i!=5]
seed=dec(source["seed"]<<1)
halftrace=sum((seed**(1<<(2*j)) for j in range(21)),F.zero())
assert halftrace**2+halftrace==seed
H=(halftrace**2)**(1<<24)
C=1+H
assert C
product_basis=[(dec((1<<bit)<<1)*dec(((1<<bit)<<1)^(source["seed"]<<1)))**(1<<24)
               for bit in bits]
t=dec(fixture["public_reciprocal"])
expected=defaultdict(set)
by_state={}
for row in table:
    expected[row["code"]].add(row["w"])
    by_state[row["final_state_id"]]=row
assert len(expected)==71 and len(by_state)==284
assert all(len(roots)==4 for roots in expected.values())


def code_of(state):
    mask=state["masks"][0]
    return sum(((mask>>bit)&1)<<j for j,bit in enumerate(bits))


cases={}
per_state=0
exceptional_A=0
for code in sorted(expected):
    p=sum((product_basis[j] for j in range(8) if code>>j&1),F.zero())
    pair=C*Z**2+p*Z+H
    pair_roots=pair.roots()
    assert pair.degree()==2 and len(pair_roots)==2
    assert all(multiplicity==1 and root for root,multiplicity in pair_roots)
    branches=[]
    for pair_root,_ in pair_roots:
        A=1+(t*pair_root)**2
        B=t*pair_root
        D=t**2+pair_root**2
        exceptional_A+=int(A==0)
        s3=A*Z**2+B*Z+D
        roots=s3.roots()
        assert len(roots)==2 and all(multiplicity==1 for _,multiplicity in roots)
        branches.append({"pair_reciprocal":enc(pair_root),
                         "final_roots":sorted(enc(root) for root,_ in roots),
                         "s3_degree":int(s3.degree())})
    found={w for row in branches for w in row["final_roots"]}
    assert found==expected[code] and len(found)==4
    cases[str(code)]=branches

for state_id,state in enumerate(source["states"][4]):
    row=by_state[state_id]
    code=code_of(state)
    assert row["code"]==code
    x=dec(state["point"][0])
    assert x
    pair_reciprocal=enc(1/x)
    matching=[branch for branch in cases[str(code)]
              if branch["pair_reciprocal"]==pair_reciprocal]
    assert len(matching)==1 and row["w"] in matching[0]["final_roots"]
    per_state+=1

finished=time.monotonic()
signal.alarm(0)
out={"status":"PASS_ALL_N41_FINAL_ROOTS_FROM_TWO_QUADRATICS",
     "candidate_id":None,"curve_id":source["curve_id"],
     "public_point":fixture["public_point"],
     "codes_checked":len(cases),"signed_states_checked":per_state,
     "pair_quadratic_roots":2*len(cases),"s3_quadratic_roots":4*len(cases),
     "s3_zero_leading_cases":exceptional_A,
     "branches_by_code":cases,
     "wall_seconds":finished-started,
     "self_maxrss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     "protocol_sha256":sha(HERE/"audit_protocol.json")}
(HERE/"audit_result.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
print(json.dumps({k:out[k] for k in ("status","codes_checked","signed_states_checked",
                                   "pair_quadratic_roots","s3_quadratic_roots",
                                   "s3_zero_leading_cases","wall_seconds",
                                   "self_maxrss_bytes")},sort_keys=True))
