"""Independent checked-Sage model and complete pair-mask replay."""
import gzip
import hashlib
import json
from pathlib import Path
from sage.all import EllipticCurve, GF, QQ

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / "result.json").read_text())
parent = json.loads((HERE.parent / "xedni-fixed-curve-admission-20261115" / "result.json").read_text())
assert result["status"] == parent["status"] == "PASS"
E0 = EllipticCurve(QQ, [-1, -2])
P0 = E0(2, 2)
queries = tests = admitted_pairs = constructions = 0
for field, old in zip(result["fields"], parent["fields"]):
    p, q = field["field_prime"], field["subgroup_order"]
    assert p == old["field_prime"] and q == old["subgroup_order"]
    Ebase = EllipticCurve(GF(p), [-1, -2])
    Pbase = Ebase(2, 2)
    m = old["subgroup_multiplier_m"]
    G = m * Pbase
    Q = 17 * G
    points = [Q - t * G for t in range(q)]
    images = []
    for model in field["models"]:
        j, a = model["j"], model["shift_a"]
        assert a == j * p
        coeffs = [0, -3*a, 0, 3*a*a-1, -a*a*a+a-2]
        assert model["coefficients"] == coeffs
        Ej = EllipticCurve(QQ, coeffs)
        assert Ej.discriminant() == E0.discriminant()
        Pj = Ej(2+a, 2)
        assert model["generator"] == [2+a, 2]
        for k in range(-4, 5):
            U, V = k * P0, k * Pj
            assert U.is_zero() == V.is_zero()
            if not U.is_zero():
                assert V[0] == U[0] + a and V[1] == U[1]
        Ejmod = Ej.change_ring(GF(p))
        assert Ejmod.a_invariants() == Ebase.a_invariants()
        Pjmod = Ejmod(2+a, 2)
        assert Pjmod == Pbase
        image = {k * Pjmod for k in range(-4, 5)}
        offsets = [t for t, R in enumerate(points) if R in image]
        assert offsets == model["bounded_image_offsets"] == old["admitted_offsets"]
        images.append(set(offsets))
        constructions += 1
    assert len(images) == 4 and all(x == images[0] for x in images)
    raw = HERE / field["raw_path"]
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == field["raw_sha256"]
    count = 0
    with gzip.open(raw, "rt") as rows:
        for t1 in range(q):
            for t2 in range(q):
                row = json.loads(next(rows))
                assert row["t"] == [t1, t2]
                mask = sum((1 << j) for j, image in enumerate(images)
                           if t1 in image and t2 in image)
                assert row["mask"] == mask
                count += mask != 0
        assert next(rows, None) is None
    assert count == field["union_admitted_pairs"] == old["admitted_full_pair_support"]
    assert field["new_pairs_from_extra_models"] == 0
    assert field["candidate_pair_tests"] == 4 * q * q
    queries += q * q
    tests += 4 * q * q
    admitted_pairs += count
assert result["totals"] == {"queries": queries, "model_constructions": constructions,
                            "candidate_pair_tests": tests,
                            "union_admitted_pairs": admitted_pairs,
                            "new_pairs_from_extra_models": 0}
print(json.dumps({"schema": "xedni-isomorphic-family-admission-audit-v1",
                  "status": "PASS", "fields": 8, "queries": queries,
                  "model_constructions": constructions,
                  "candidate_pair_tests": tests,
                  "union_admitted_pairs": admitted_pairs}, sort_keys=True, indent=2))
