"""Apply a frozen vector-dependent rank-one lift before public relation tests."""
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
assert len(vectors) == 13
assert len(registry["fields"]) == 8
offsets = [0, 1, 2, 3, 5, 8, 13, 21]
deadline = time.monotonic() + protocol["run_cap_seconds"]
counts = Counter()
rows_path = HERE / "rows.jsonl"


def xy(point):
    return None if point.is_zero() else [str(point[0]), str(point[1])]


def centered(value, prime):
    n = int(value)
    return n if n <= prime // 2 else n - prime


def attempt(kind, prime, q, G, target, w, j, t1, t2, U, V, a, b):
    counts["attempts"] += 1
    T = (pow(b % q, -1, q) * U)
    x, y = centered(T[0], prime), centered(T[1], prime)
    B = y*y-x*x*x+x
    rational = EllipticCurve(QQ, [-1, B])
    P = rational(QQ(x), QQ(y))
    A, C = b*P, -a*P
    rational_relation = bool((a*A+b*C).is_zero())
    finite = EllipticCurve(GF(prime), [-1, -2])
    assert finite.discriminant() != 0 and rational.discriminant() != 0
    reduction_A = finite(GF(prime)(A[0]), GF(prime)(A[1]))
    reduction_C = finite(GF(prime)(C[0]), GF(prime)(C[1]))
    match_A = bool(reduction_A == U)
    match_C = bool(reduction_C == V)
    accepted = rational_relation and match_A and match_C
    public_relation = bool((a*U+b*V).is_zero())
    assert rational_relation and match_A and accepted == public_relation
    counts[kind+"_attempts"] += 1
    counts[kind+"_accepted"] += int(accepted)
    counts[kind+"_rejected"] += int(not accepted)
    counts[kind+"_public_relations"] += int(public_relation)
    return {"kind": kind, "field_prime": prime, "subgroup_order": q, "target_index": j,
            "fixture_scalar": w, "target": xy(target), "offsets": [t1,t2],
            "public_points": [xy(U),xy(V)], "vector": [a,b], "common_finite_point": xy(T),
            "lift_point": [x,y], "rational_B": str(B),
            "rational_points": [xy(A),xy(C)], "rational_relation": rational_relation,
            "reduced_points": [xy(reduction_A),xy(reduction_C)],
            "first_reduction_match": match_A, "second_reduction_match": match_C,
            "accepted": accepted, "public_relation_diagnostic": public_relation,
            "status": "accepted" if accepted else "second_reduction_mismatch"}


with rows_path.open("w") as stream:
    for field in registry["fields"]:
        p, q = field["field_prime"], field["subgroup_order"]
        finite = EllipticCurve(GF(p), [-1, -2])
        G = finite(*field["generator"])
        assert q*G == finite(0)
        assert all(b % q for _, b in vectors)
        for j in range(4):
            digest = hashlib.sha256(f"xedni-precommitted-v1|{p}|{j}".encode()).digest()
            w = 1 + int.from_bytes(digest, "big") % (q-1)
            assert w == protocol["target_scalars_by_field"][str(p)][j]
            target = w*G
            queries = []
            for t1 in offsets:
                for t2 in offsets:
                    U, V = target-t1*G, target-t2*G
                    if t1 != t2 and not U.is_zero() and not V.is_zero():
                        queries.append((t1,t2,U,V))
            assert len(queries) >= 16
            for t1,t2,U,V in queries[:16]:
                for a,b in vectors:
                    if time.monotonic() >= deadline:
                        break
                    row = attempt("selected",p,q,G,target,w,j,t1,t2,U,V,a,b)
                    stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
                if time.monotonic() >= deadline:
                    break
            if time.monotonic() >= deadline:
                break
            t1 = 0
            t2 = (3*w*pow(2,-1,q)) % q
            U,V = target-t1*G,target-t2*G
            assert t1 != t2 and not U.is_zero() and not V.is_zero()
            positive = attempt("positive_control",p,q,G,target,w,j,t1,t2,U,V,1,2)
            assert positive["accepted"]
            stream.write(json.dumps(positive, sort_keys=True, separators=(",", ":")) + "\n")
            for k in range(1,q):
                tn = (t2+k) % q
                Un,Vn = target, target-tn*G
                if tn != 0 and not Vn.is_zero() and not (Un+2*Vn).is_zero():
                    negative = attempt("negative_control",p,q,G,target,w,j,0,tn,Un,Vn,1,2)
                    assert not negative["accepted"]
                    stream.write(json.dumps(negative, sort_keys=True, separators=(",", ":")) + "\n")
                    break
            else:
                raise AssertionError("negative control unavailable")
        if time.monotonic() >= deadline:
            break

status = "complete" if counts["selected_attempts"] == 6656 and counts["positive_control_attempts"] == 32 and counts["negative_control_attempts"] == 32 else "capped_900s"
result = {"schema": "xedni-precommitted-vector-lift-result-v1", "status": status,
          "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
          "registry_sha256": protocol["field_registry_sha256"],
          "family_sha256": protocol["selected_family_sha256"],
          "counts": dict(counts), "rows_sha256": hashlib.sha256(rows_path.read_bytes()).hexdigest()}
(HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
