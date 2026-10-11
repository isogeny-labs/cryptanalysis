"""Independent Sage arithmetic and group audit of the native-integer scan."""

import hashlib
import json
import random
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
GEOMETRY = BASE / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json"
PRIOR_AUDIT = BASE / "n41_symbolic_two_bucket_20261011/audit.json"


def dec(field, word):
    return sum((field.gen()**i for i in range(41) if word >> i & 1), field.zero())


def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial()))


def roots(a, b, c):
    field = c.parent()
    if not b:
        return [(c/a)**(1 << 40)]
    v = a*c/(b*b)
    if v.trace() != 0:
        return []
    h = field.zero()
    q = v
    for _ in range(21):
        h += q
        q = q**4
    scale = b/a
    return [scale*h, scale*(h+1)]


def selected(values, mask):
    return sum((value for i, value in enumerate(values) if mask >> i & 1),
               values[0].parent().zero())


def seed_roots(basis_u, seed):
    us = selected(basis_u, seed)
    ws = us*us+us
    basis_w = [u*u+u for u in basis_u]
    products = {selected(basis_w, a)**2+ws*selected(basis_w, a)
                for a in range(64)}
    assert len(products) == 32
    return {z for p in products for z in roots(1+p, p, us*us)}


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    targets = json.loads((HERE / "targets.json").read_text())
    assert hashlib.sha256((HERE / "run.py").read_bytes()).hexdigest() == protocol["sha256"]["source"]
    assert hashlib.sha256(GEOMETRY.read_bytes()).hexdigest() == protocol["sha256"]["geometry"]
    assert hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest() == result["protocol_sha256"]
    binary = PolynomialRing(GF(2), "t")
    t = binary.gen()
    field = GF(2**41, "t", modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    source = json.loads(GEOMETRY.read_text())["n41"]
    left_u = [dec(field, x) for x in source["window_basis_halftrace"][2]]
    right_u = [dec(field, x) for x in source["window_basis_halftrace"][3]]
    left_roots = seed_roots(left_u, 16)
    right_roots = {s: seed_roots(right_u, s) for s in (5, 17)}
    rng = random.Random(20261011)
    for _ in range(128):
        a, b = rng.randrange(1 << 41), rng.randrange(1 << 41)
        word = 0
        x, y = a, b
        mod = (1 << 41) | (1 << 3) | 1
        while y:
            if y & 1:
                word ^= x
            y >>= 1
            x <<= 1
            if x & (1 << 41):
                x ^= mod
        assert word == enc(dec(field, a)*dec(field, b))
    checks = []
    for row, target in zip(result["rows"], targets["rows"]):
        assert (row["kind"], row["option"]) == (target["kind"], target["option"])
        point = curve(*(dec(field, x) for x in target["raw_xy"]))
        q = 1/(point[0]+1)
        assert enc(q) == target["target_z"]
        for right_seed, domain in right_roots.items():
            hits = []
            for a in left_roots:
                for b in domain:
                    c = (a*a+a)*(q*q+q)
                    # Exact transformed-coordinate S3 equation.
                    if (1+c)*b*b+c*b+(a+q)**2 == 0:
                        hits.append(enc(a))
                        break
            archived = next(x for x in json.loads(PRIOR_AUDIT.read_text())["direct_case_checks"]
                            if x["kind"] == row["kind"] and x["option"] == row["option"])
            if right_seed == 5:
                assert sorted(set(hits)) == archived["roots"]
            predicted = sorted(h["left_z"] for h in row["hits"]
                               if h["left_seed"] == 16 and h["right_seed"] == right_seed)
            if row["status"] == "COMPLETE":
                assert predicted == sorted(set(hits))
            checks.append({"kind": row["kind"], "option": row["option"],
                           "right_seed": right_seed, "left_seed": 16,
                           "roots": sorted(set(hits)), "row_complete": row["status"] == "COMPLETE"})
    positive = next(x for x in result["rows"] if x["kind"] == "positive" and x["option"] == 3)
    assert positive["hits"] == [{"left_seed": 16, "right_seed": 5,
                                  "left_z": 585190544792}]
    witness = json.loads(PRIOR_AUDIT.read_text())["positive_raw_group_witness"]
    L = curve(*(dec(field, x) for x in witness["left"]))
    R = curve(*(dec(field, x) for x in witness["right"]))
    T = curve(*(dec(field, x) for x in witness["target"]))
    assert L+R == T
    assert enc(1/(L[0]+1)) == positive["hits"][0]["left_z"]
    output = {"status": "PASS_EXACT_REPLAY", "field_multiplication_checks": 128,
              "selected_seed_panel": checks, "positive_raw_group_sum": True,
              "result_sha256": hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest(),
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE / "audit.json").write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": output["status"], "seed_checks": len(checks)}))


if __name__ == "__main__":
    main()
