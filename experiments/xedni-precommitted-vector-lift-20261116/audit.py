"""Pure-Python replay of every finite and rational group computation."""
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
family_path = ROOT / "xedni-coefficient-optimization-20261115" / "family-selection.json"
assert hashlib.sha256(registry_path.read_bytes()).hexdigest() == protocol["field_registry_sha256"]
assert hashlib.sha256(family_path.read_bytes()).hexdigest() == protocol["selected_family_sha256"]
assert hashlib.sha256((HERE / "rows.jsonl").read_bytes()).hexdigest() == result["rows_sha256"]
registry = json.loads(registry_path.read_text())
vectors = [tuple(v) for v in json.loads(family_path.read_text())["selected"]]
rows = iter((HERE / "rows.jsonl").open())
counts = Counter()
offsets = [0, 1, 2, 3, 5, 8, 13, 21]


def add(P, Q, A, B, prime=None):
    if P is None:
        return Q
    if Q is None:
        return P
    x1,y1 = P
    x2,y2 = Q
    if prime is None:
        if x1 == x2 and y1 + y2 == 0:
            return None
        slope = (3*x1*x1+A)/(2*y1) if P == Q else (y2-y1)/(x2-x1)
        x3 = slope*slope-x1-x2
        return x3, slope*(x1-x3)-y1
    if x1 == x2 and (y1+y2) % prime == 0:
        return None
    numerator, denominator = ((3*x1*x1+A,2*y1) if P == Q else (y2-y1,x2-x1))
    slope = numerator*pow(int(denominator)%prime,-1,prime) % prime
    x3 = (slope*slope-x1-x2) % prime
    return x3, (slope*(x1-x3)-y1) % prime


def mul(n,P,A,B,prime=None):
    if n < 0:
        x,y = P
        P = (x,-y if prime is None else (-y)%prime)
        n = -n
    out = None
    while n:
        if n & 1:
            out = add(out,P,A,B,prime)
        P = add(P,P,A,B,prime)
        n >>= 1
    return out


def finite_fraction(q,p):
    q = Fraction(q)
    assert q.denominator % p != 0
    return q.numerator*pow(q.denominator,-1,p) % p


def point_record(P):
    return None if P is None else [str(P[0]),str(P[1])]


def check(kind,p,q,j,w,G,target,t1,t2,U,V,a,b):
    row = json.loads(next(rows))
    assert row["kind"] == kind and row["field_prime"] == p and row["subgroup_order"] == q
    assert row["target_index"] == j and row["fixture_scalar"] == w
    assert row["target"] == point_record(target)
    assert row["offsets"] == [t1,t2] and row["vector"] == [a,b]
    assert row["public_points"] == [point_record(U),point_record(V)]
    T = mul(pow(b%q,-1,q),U,-1,-2,p)
    assert row["common_finite_point"] == point_record(T)
    x,y = T
    x = x if x <= p//2 else x-p
    y = y if y <= p//2 else y-p
    B = y*y-x*x*x+x
    assert row["lift_point"] == [x,y] and row["rational_B"] == str(B)
    P = Fraction(x),Fraction(y)
    assert P[1]*P[1] == P[0]**3-P[0]+B
    A,C = mul(b,P,-1,B),mul(-a,P,-1,B)
    assert row["rational_points"] == [point_record(A),point_record(C)]
    relation = add(mul(a,A,-1,B),mul(b,C,-1,B),-1,B) is None
    assert row["rational_relation"] == relation is True
    red_A = tuple(finite_fraction(v,p) for v in A)
    red_C = tuple(finite_fraction(v,p) for v in C)
    assert row["reduced_points"] == [point_record(red_A),point_record(red_C)]
    match_A,match_C = red_A == U,red_C == V
    public = add(mul(a,U,-1,-2,p),mul(b,V,-1,-2,p),-1,-2,p) is None
    accepted = relation and match_A and match_C
    assert row["first_reduction_match"] == match_A is True
    assert row["second_reduction_match"] == match_C
    assert row["public_relation_diagnostic"] == public
    assert row["accepted"] == accepted == public
    assert row["status"] == ("accepted" if accepted else "second_reduction_mismatch")
    if accepted:
        assert (a+b)%q != 0
        recovered = (a*t1+b*t2)*pow((a+b)%q,-1,q) % q
        assert recovered == w and mul(recovered,G,-1,-2,p) == target
    counts[kind+"_attempts"] += 1
    counts[kind+"_accepted"] += int(accepted)
    counts[kind+"_rejected"] += int(not accepted)
    counts[kind+"_public_relations"] += int(public)
    counts["attempts"] += 1


for field in registry["fields"]:
    p,q = field["field_prime"],field["subgroup_order"]
    G = tuple(field["generator"])
    assert mul(q,G,-1,-2,p) is None
    for j in range(4):
        digest = hashlib.sha256(f"xedni-precommitted-v1|{p}|{j}".encode()).digest()
        w = 1+int.from_bytes(digest,"big")%(q-1)
        assert w == protocol["target_scalars_by_field"][str(p)][j]
        target = mul(w,G,-1,-2,p)
        queries = []
        for t1 in offsets:
            for t2 in offsets:
                U = add(target,mul(-t1,G,-1,-2,p),-1,-2,p)
                V = add(target,mul(-t2,G,-1,-2,p),-1,-2,p)
                if t1 != t2 and U is not None and V is not None:
                    queries.append((t1,t2,U,V))
        for t1,t2,U,V in queries[:16]:
            for a,b in vectors:
                check("selected",p,q,j,w,G,target,t1,t2,U,V,a,b)
        t1 = 0
        t2 = 3*w*pow(2,-1,q)%q
        U = target
        V = add(target,mul(-t2,G,-1,-2,p),-1,-2,p)
        check("positive_control",p,q,j,w,G,target,t1,t2,U,V,1,2)
        for k in range(1,q):
            tn = (t2+k)%q
            Vn = add(target,mul(-tn,G,-1,-2,p),-1,-2,p)
            if tn != 0 and Vn is not None and add(U,mul(2,Vn,-1,-2,p),-1,-2,p) is not None:
                check("negative_control",p,q,j,w,G,target,0,tn,U,Vn,1,2)
                break
        else:
            raise AssertionError("negative control unavailable")
assert next(rows,None) is None
assert dict(counts) == result["counts"]
assert counts["attempts"] == 6720
receipt = {"status":"PASS","attempts":6720,"selected_attempts":6656,
           "selected_accepted":counts["selected_accepted"],
           "positive_controls":counts["positive_control_accepted"],
           "negative_controls":counts["negative_control_rejected"],
           "method":"independent Python finite and rational short-Weierstrass group laws"}
(HERE/"audit.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,sort_keys=True))
