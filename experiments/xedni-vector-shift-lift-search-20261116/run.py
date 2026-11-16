"""Precommitted vector-specific two-point rational lift search."""
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / "protocol.json").read_text())
registry_path = ROOT / "xedni-crt-band-panel-20261115" / "result.json"
family_path = ROOT / "xedni-coefficient-optimization-20261115" / "family-selection.json"
assert hashlib.sha256(registry_path.read_bytes()).hexdigest() == protocol["field_registry_sha256"]
assert hashlib.sha256(family_path.read_bytes()).hexdigest() == protocol["selected_family_sha256"]
registry = json.loads(registry_path.read_text())
vectors = [tuple(v) for v in json.loads(family_path.read_text())["selected"]]
assert len(vectors) == 13 and len(registry["fields"]) == 8
offsets = [0, 1, 2, 3, 5, 8, 13, 21]
deadline = time.monotonic() + protocol["run_cap_seconds"]
counts = Counter()
rows_path = HERE / "rows.jsonl"


def xy(point):
    return None if point.is_zero() else [int(point[0]), int(point[1])]


def centered(value, p):
    n = int(value)
    return n if n <= p//2 else n-p


def run_control(p, label, multiplier):
    rational = EllipticCurve(QQ, [-1, -2])
    P = rational(2, 2)
    Q = multiplier*P
    relation = bool((2*P-Q).is_zero())
    finite = EllipticCurve(GF(p), [-1, -2])
    rP = finite(GF(p)(P[0]), GF(p)(P[1]))
    rQ = finite(GF(p)(Q[0]), GF(p)(Q[1]))
    reduced = bool((2*rP-rQ).is_zero())
    assert relation == (multiplier == 2)
    counts[label] += 1
    return {"kind": label, "field_prime": p, "vector": [2, -1],
            "rational_points": [[str(P[0]),str(P[1])],[str(Q[0]),str(Q[1])]],
            "rational_relation": relation, "reduced_relation": reduced,
            "status": "pass" if relation == (multiplier == 2) else "failed"}


def attempt(p, q, target_index, w, t1, t2, U, V, a, b, candidate_index):
    counts["candidate_attempts"] += 1
    pattern = [(0,0,0,0),(a,0,0,0),(0,b,0,0),(a,b,-a,-b)][candidate_index]
    original = [(centered(T[0],p), centered(T[1],p)) for T in (U,V)]
    x1,y1 = original[0][0]+p*pattern[0], original[0][1]+p*pattern[1]
    x2,y2 = original[1][0]+p*pattern[2], original[1][1]+p*pattern[3]
    public_relation = None
    record = {"kind":"candidate","field_prime":p,"subgroup_order":q,
              "target_index":target_index,"fixture_scalar":w,"offsets":[t1,t2],
              "public_points":[xy(U),xy(V)],"vector":[a,b],
              "candidate_index":candidate_index,"shift":list(pattern),
              "lifted_points":[[x1,y1],[x2,y2]],"A":None,"B":None,
              "rational_relation":None,"public_relation_diagnostic":None,
              "status":None}
    try:
        if x1 == x2:
            record["status"] = "same_x"
        else:
            v1, v2 = QQ(y1*y1-x1**3), QQ(y2*y2-x2**3)
            A = (v1-v2)/QQ(x1-x2)
            B = v1-A*x1
            record["A"],record["B"] = str(A),str(B)
            if 4*A**3+27*B**2 == 0:
                record["status"] = "singular"
            elif A.denominator()%p == 0 or B.denominator()%p == 0:
                record["status"] = "nonintegral"
            elif GF(p)(A) != GF(p)(-1) or GF(p)(B) != GF(p)(-2):
                record["status"] = "wrong_reduction"
            else:
                rational = EllipticCurve(QQ, [A,B])
                P,Q = rational(x1,y1),rational(x2,y2)
                if GF(p)(rational.discriminant()) == 0:
                    record["status"] = "bad_reduction"
                else:
                    finite = EllipticCurve(GF(p),[-1,-2])
                    assert finite(GF(p)(x1),GF(p)(y1)) == U
                    assert finite(GF(p)(x2),GF(p)(y2)) == V
                    relation = bool((a*P+b*Q).is_zero())
                    record["rational_relation"] = relation
                    record["status"] = "rational_relation" if relation else "no_rational_relation"
    except Exception as error:
        record["status"] = "producer_failure"
        record["error"] = f"{type(error).__name__}: {error}"
    public_relation = bool((a*U+b*V).is_zero())
    record["public_relation_diagnostic"] = public_relation
    counts[record["status"]] += 1
    counts["public_relation_candidate_attempts"] += int(public_relation)
    if record["rational_relation"]:
        assert public_relation
    return record


with rows_path.open("w") as stream:
    for field in registry["fields"]:
        p,q = field["field_prime"],field["subgroup_order"]
        for label,multiplier in (("positive_control",2),("negative_control",3)):
            stream.write(json.dumps(run_control(p,label,multiplier),sort_keys=True,separators=(",", ":"))+"\n")
        finite = EllipticCurve(GF(p),[-1,-2])
        G = finite(*field["generator"])
        assert (q*G).is_zero()
        for j in range(4):
            digest = hashlib.sha256(f"xedni-vector-shift-v1|{p}|{j}".encode()).digest()
            w = 1+int.from_bytes(digest,"big")%(q-1)
            assert w == protocol["target_scalars_by_field"][str(p)][j]
            target = w*G
            queries = []
            for t1 in offsets:
                for t2 in offsets:
                    U,V = target-t1*G,target-t2*G
                    if t1 != t2 and not U.is_zero() and not V.is_zero():
                        queries.append((t1,t2,U,V))
            assert len(queries) >= 16
            for t1,t2,U,V in queries[:16]:
                for a,b in vectors:
                    for k in range(4):
                        if time.monotonic() >= deadline:
                            break
                        row = attempt(p,q,j,w,t1,t2,U,V,a,b,k)
                        stream.write(json.dumps(row,sort_keys=True,separators=(",", ":"))+"\n")
                    if time.monotonic() >= deadline:
                        break
                if time.monotonic() >= deadline:
                    break
            if time.monotonic() >= deadline:
                break
        print(p,counts["candidate_attempts"],flush=True)
        if time.monotonic() >= deadline:
            break

status = "complete" if counts["candidate_attempts"] == 26624 and counts["producer_failure"] == 0 else "capped_or_failed"
result = {"schema":"xedni-vector-shift-lift-search-result-v1","status":status,
          "protocol_sha256":hashlib.sha256((HERE/"protocol.json").read_bytes()).hexdigest(),
          "registry_sha256":protocol["field_registry_sha256"],"family_sha256":protocol["selected_family_sha256"],
          "counts":dict(counts),"rows_sha256":hashlib.sha256(rows_path.read_bytes()).hexdigest()}
(HERE/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,indent=2,sort_keys=True))
