"""Independent exact replay of all vector-specific shifted-lift candidates."""
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
raw_rows = iter((HERE / "rows.jsonl").open())
counts = Counter()
hits = []
offsets = [0, 1, 2, 3, 5, 8, 13, 21]


def add(P, Q, A, B, prime=None):
    if P is None:
        return Q
    if Q is None:
        return P
    x1,y1 = P
    x2,y2 = Q
    if prime is None:
        if x1 == x2 and y1+y2 == 0:
            return None
        slope = (3*x1*x1+A)/(2*y1) if P == Q else (y2-y1)/(x2-x1)
        x3 = slope*slope-x1-x2
        return x3,slope*(x1-x3)-y1
    if x1 == x2 and (y1+y2)%prime == 0:
        return None
    numerator,denominator = ((3*x1*x1+A,2*y1) if P == Q else (y2-y1,x2-x1))
    slope = numerator*pow(int(denominator)%prime,-1,prime)%prime
    x3 = (slope*slope-x1-x2)%prime
    return x3,(slope*(x1-x3)-y1)%prime


def mul(n,P,A,B,prime=None):
    if n < 0:
        x,y = P
        P = x,(-y if prime is None else (-y)%prime)
        n = -n
    out = None
    while n:
        if n & 1:
            out = add(out,P,A,B,prime)
        P = add(P,P,A,B,prime)
        n >>= 1
    return out


def field(q,p):
    q = Fraction(q)
    assert q.denominator%p != 0
    return q.numerator*pow(q.denominator,-1,p)%p


def affine(P):
    return None if P is None else [str(P[0]),str(P[1])]


def control(p,label,multiplier):
    row = json.loads(next(raw_rows))
    P = Fraction(2),Fraction(2)
    Q = mul(multiplier,P,-1,Fraction(-2))
    assert row["kind"] == label and row["field_prime"] == p and row["vector"] == [2,-1]
    assert row["rational_points"] == [affine(P),affine(Q)]
    relation = add(mul(2,P,-1,Fraction(-2)),mul(-1,Q,-1,Fraction(-2)),-1,Fraction(-2)) is None
    assert row["rational_relation"] == relation == (multiplier == 2)
    rP = tuple(field(v,p) for v in P)
    rQ = tuple(field(v,p) for v in Q)
    reduced = add(mul(2,rP,-1,-2,p),mul(-1,rQ,-1,-2,p),-1,-2,p) is None
    assert row["reduced_relation"] == reduced
    assert row["status"] == "pass"
    counts[label] += 1


def candidate(p,q,j,w,t1,t2,U,V,a,b,k):
    row = json.loads(next(raw_rows))
    assert row["kind"] == "candidate" and row["field_prime"] == p and row["subgroup_order"] == q
    assert row["target_index"] == j and row["fixture_scalar"] == w
    assert row["offsets"] == [t1,t2] and row["public_points"] == [list(U),list(V)]
    assert row["vector"] == [a,b] and row["candidate_index"] == k
    pattern = [(0,0,0,0),(a,0,0,0),(0,b,0,0),(a,b,-a,-b)][k]
    assert row["shift"] == list(pattern)
    original = [(x if x<=p//2 else x-p,y if y<=p//2 else y-p) for x,y in (U,V)]
    x1,y1 = original[0][0]+p*pattern[0],original[0][1]+p*pattern[1]
    x2,y2 = original[1][0]+p*pattern[2],original[1][1]+p*pattern[3]
    assert row["lifted_points"] == [[x1,y1],[x2,y2]]
    relation = None
    A = B = None
    if x1 == x2:
        status = "same_x"
    else:
        v1 = Fraction(y1*y1-x1**3)
        v2 = Fraction(y2*y2-x2**3)
        A = (v1-v2)/Fraction(x1-x2)
        B = v1-A*x1
        assert row["A"] == str(A) and row["B"] == str(B)
        if 4*A**3+27*B**2 == 0:
            status = "singular"
        elif A.denominator%p == 0 or B.denominator%p == 0:
            status = "nonintegral"
        elif field(A,p) != (-1)%p or field(B,p) != (-2)%p:
            status = "wrong_reduction"
        else:
            assert (y1*y1-x1**3-A*x1-B) == 0
            assert (y2*y2-x2**3-A*x2-B) == 0
            if field(-16*(4*A**3+27*B**2),p) == 0:
                status = "bad_reduction"
            else:
                P = Fraction(x1),Fraction(y1)
                Q = Fraction(x2),Fraction(y2)
                relation = add(mul(a,P,A,B),mul(b,Q,A,B),A,B) is None
                status = "rational_relation" if relation else "no_rational_relation"
    assert row["status"] == status and row["rational_relation"] == relation
    if status == "same_x":
        assert row["A"] is None and row["B"] is None
    public = add(mul(a,U,-1,-2,p),mul(b,V,-1,-2,p),-1,-2,p) is None
    assert row["public_relation_diagnostic"] == public
    if relation:
        assert public and (a+b)%q != 0
        recovered = (a*t1+b*t2)*pow((a+b)%q,-1,q)%q
        assert recovered == w
        hits.append({"field_prime":p,"subgroup_order":q,"target_index":j,
                     "candidate_ordinal_one_based":counts["candidate_attempts"]+1,
                     "fixture_scalar":w,"offsets":[t1,t2],"vector":[a,b],
                     "candidate_index":k,"lifted_points":[[x1,y1],[x2,y2]],
                     "A":str(A),"B":str(B),"recovered_scalar":recovered})
    counts["candidate_attempts"] += 1
    counts[status] += 1
    counts["public_relation_candidate_attempts"] += int(public)


for entry in registry["fields"]:
    p,q = entry["field_prime"],entry["subgroup_order"]
    control(p,"positive_control",2)
    control(p,"negative_control",3)
    G = tuple(entry["generator"])
    assert mul(q,G,-1,-2,p) is None
    for j in range(4):
        digest = hashlib.sha256(f"xedni-vector-shift-v1|{p}|{j}".encode()).digest()
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
        assert len(queries) >= 16
        for t1,t2,U,V in queries[:16]:
            for a,b in vectors:
                for k in range(4):
                    candidate(p,q,j,w,t1,t2,U,V,a,b,k)
assert next(raw_rows,None) is None
assert dict(counts) == result["counts"]
assert len(hits) == 1 and counts["candidate_attempts"] == 26624
receipt = {"status":"PASS","candidate_attempts":26624,
           "rational_relation_hits":len(hits),"public_relation_candidate_attempts":counts["public_relation_candidate_attempts"],
           "positive_controls":counts["positive_control"],"negative_controls":counts["negative_control"],
           "method":"independent Python finite and rational short-Weierstrass group laws"}
(HERE/"audit.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
(HERE/"hit.json").write_text(json.dumps(hits[0],indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,sort_keys=True))
