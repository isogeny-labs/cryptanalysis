"""Independent exact replay using Python finite and rational curve laws."""
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / "protocol.json").read_text())
result = json.loads((HERE / "result.json").read_text())
registry_path = ROOT / "xedni-crt-band-panel-20261115" / "result.json"
source_path = ROOT / "xedni-vector-shift-lift-search-20261116" / "rows.jsonl"
family_path = ROOT / "xedni-coefficient-optimization-20261115" / "family-selection.json"
assert hashlib.sha256(registry_path.read_bytes()).hexdigest() == protocol["source_registry_sha256"]
assert hashlib.sha256(source_path.read_bytes()).hexdigest() == protocol["source_rows_sha256"]
assert hashlib.sha256(family_path.read_bytes()).hexdigest() == protocol["selected_family_sha256"]
for name, digest in (("screen.jsonl","screen_sha256"),("lifts.jsonl","lifts_sha256")):
    assert hashlib.sha256((HERE/name).read_bytes()).hexdigest() == result[digest]
fields = {f["field_prime"]: f for f in json.loads(registry_path.read_text())["fields"]}
vectors = {tuple(v) for v in json.loads(family_path.read_text())["selected"]}
expected=[]
seen=set()
for line in source_path.open():
    raw=json.loads(line)
    if raw.get("kind")!="candidate":
        continue
    key=(raw["field_prime"],raw["target_index"],*raw["offsets"],*raw["vector"])
    if key in seen:
        continue
    seen.add(key)
    assert tuple(raw["vector"]) in vectors
    expected.append(raw)
assert len(expected)==6656


def add(P,Q,A,p=None):
    if P is None:
        return Q
    if Q is None:
        return P
    x,y=P
    u,v=Q
    if p is None:
        if x == u and y+v == 0:
            return None
        m = (3*x*x+A)/(2*y) if P==Q else (v-y)/(u-x)
        X=m*m-x-u
        return X,m*(x-X)-y
    if x == u and (y+v)%p == 0:
        return None
    num,den=(3*x*x+A,2*y) if P==Q else (v-y,u-x)
    m=num*pow(den%p,-1,p)%p
    X=(m*m-x-u)%p
    return X,(m*(x-X)-y)%p


def mul(n,P,A,p=None):
    if n < 0:
        P=(P[0],-P[1] if p is None else (-P[1])%p)
        n=-n
    R=None
    while n:
        if n & 1:
            R=add(R,P,A,p)
        P=add(P,P,A,p)
        n >>= 1
    return R


def reduce_coord(z,p):
    z=Fraction(z)
    assert z.denominator%p != 0
    return z.numerator*pow(z.denominator,-1,p)%p


def packed(P):
    return None if P is None else list(P)


counts=Counter()
negative_by_field=Counter()
selected=[]
screen_lines=(HERE/"screen.jsonl").read_text().splitlines()
assert len(screen_lines)==len(expected)
for raw,line in zip(expected,screen_lines):
    row=json.loads(line)
    for key in ("field_prime","target_index","offsets","vector","fixture_scalar"):
        assert row[key]==raw[key]
    p,q,j=row["field_prime"],row["subgroup_order"],row["target_index"]
    f=fields[p]
    assert q==f["subgroup_order"]
    G=tuple(f["generator"])
    assert mul(q,G,-1,p) is None
    digest=hashlib.sha256(f"xedni-vector-shift-v1|{p}|{j}".encode()).digest()
    w=1+int.from_bytes(digest,"big")%(q-1)
    assert w==row["fixture_scalar"]
    target=mul(w,G,-1,p)
    t1,t2=row["offsets"]
    U=add(target,mul(-t1,G,-1,p),-1,p)
    V=add(target,mul(-t2,G,-1,p),-1,p)
    assert packed(U)==row["U"] and packed(V)==row["V"]
    a,b=row["vector"]
    relation=add(mul(a,U,-1,p),mul(b,V,-1,p),-1,p) is None
    assert relation==row["public_relation"]
    counts["screened"]+=1
    counts["public_relation"]+=int(relation)
    if relation or negative_by_field[p]<4:
        selected.append((row,U,V,target,G))
        if not relation:
            negative_by_field[p]+=1

lift_rows=[json.loads(line) for line in (HERE/"lifts.jsonl").open()]
assert len(selected)==len(lift_rows)==159
for (screen,U,V,target,G),row in zip(selected,lift_rows):
    assert all(row[key]==screen[key] for key in ("field_prime","subgroup_order","target_index","offsets","vector","U","V","public_relation"))
    p,q=screen["field_prime"],screen["subgroup_order"]
    a,b=screen["vector"]
    S=mul(pow(b,-1,q),U,-1,p)
    assert packed(S)==row["S"] and mul(b,S,-1,p)==U
    x=S[0] if S[0]<=p//2 else S[0]-p
    y=S[1] if S[1]<=p//2 else S[1]-p
    assert row["T"]==[x,y]
    A,B=row["A"],row["B"]
    assert A==-1 and B==y*y-x*x*x+x
    assert -16*(4*A**3+27*B**2)%p != 0
    T=(Fraction(x),Fraction(y))
    assert y*y==x*x*x+A*x+B
    P,R=mul(b,T,Fraction(A)),mul(-a,T,Fraction(A))
    assert packed(P)==[Fraction(z) for z in row["P"]]
    assert packed(R)==[Fraction(z) for z in row["R"]]
    assert add(mul(a,P,Fraction(A)),mul(b,R,Fraction(A)),Fraction(A)) is None
    rP=tuple(reduce_coord(z,p) for z in P)
    rR=tuple(reduce_coord(z,p) for z in R)
    assert packed(rP)==row["P_reduction"] and packed(rR)==row["R_reduction"]
    assert rP==U and rR==mul(-a,S,-1,p)
    assert (rR==V)==row["matches_U_V"]==screen["public_relation"]
    assert row["status"]=="pass" and row["rational_relation"]
    if screen["public_relation"]:
        t1,t2=screen["offsets"]
        recovered=(a*t1+b*t2)*pow((a+b)%q,-1,q)%q
        assert recovered==row["derived_scalar"]
        assert mul(recovered,G,-1,p)==target
        counts["positive_pass"]+=1
    else:
        assert row["kind"]=="negative_control"
        counts["negative_control_pass"]+=1
    counts["selected_lifts"]+=1

assert dict(counts)==result["counts"]
assert dict(negative_by_field)=={int(k):v for k,v in result["negative_controls_by_field"].items()}
audit={"schema":"xedni-common-preimage-lift-audit-v1","status":"PASS",
       "method":"independent Python finite and rational short-Weierstrass group laws",
       "counts":dict(sorted(counts.items())),"screen_sha256":result["screen_sha256"],
       "lifts_sha256":result["lifts_sha256"]}
(HERE/"audit.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n")
print(json.dumps(audit,indent=2,sort_keys=True))
