"""Independent symbolic S4 resultant and checked N41/N131 group controls."""

import hashlib
import itertools
import json
import random
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode(field, value, n):
    return sum((field.gen() ** i for i in range(n) if value >> i & 1), field.zero())


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial()))


def group_control(n, modulus, points):
    field = GF(2**n, "T", modulus=modulus)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    triplet = [curve(*(decode(field, value, n) for value in point)) for point in points]
    assert all(point in curve for point in triplet)
    inputs = [1 / point[0] for point in triplet]
    u = PolynomialRing(field, "w")
    w = u.gen()
    a, b, c = inputs
    A, B, C = 1 + (a*b)**2, a*b, a**2 + b**2
    D, E, F = 1 + (c*w)**2, c*w, c**2 + w**2
    poly = (A*F + D*C)**2 + (A*E + D*B)*(B*F + E*C)
    actual = set()
    for signs in itertools.product((0, 1), repeat=3):
        group = sum((-point if sign else point for point, sign in zip(triplet, signs)),
                    curve(0))
        if group and group[0]:
            actual.add(1 / group[0])
    roots = set(poly.roots(multiplicities=False))
    assert roots == actual and len(roots) == 4
    target = 1 / (sum(triplet, curve(0))[0])
    assert target in roots
    return {"input_reciprocals": [encode(value) for value in inputs],
            "target_reciprocal": encode(target),
            "field_roots": sorted(encode(value) for value in roots),
            "signed_group_x_roots": sorted(encode(value) for value in actual),
            "univariate_degree": int(poly.degree())}


def main():
    protocol = json.loads((HERE / "audit_protocol.json").read_text())
    assert protocol["status"] == "FROZEN"
    files = {"script": HERE / "audit_sage.py",
             "runtime": HERE / "sage_runtime_info.json",
             "resultant": HERE / "resultant.json",
             "symmetric": HERE / "symmetric_result.json",
             "n41_relation": GOAL / "n41_common_frob_factor_20261012/audit_result.json",
             "n131_control": GOAL / "n131_w15_onepair_fixed_sat_gate_20261010/fivepair_control_group_lift.json"}
    assert {name: sha(path) for name, path in files.items()} == protocol["sha256"]
    result = json.loads(files["resultant"].read_text())
    R = PolynomialRing(GF(2), ["a", "b", "c", "t"])
    a, b, c, t = R.gens()
    S = PolynomialRing(R, "z")
    z = S.gen()
    f = (1 + (a*b)**2)*z**2 + (a*b)*z + a**2+b**2
    g = (1 + (c*t)**2)*z**2 + (c*t)*z + c**2+t**2
    direct = f.resultant(g)
    listed = sum((a**i*b**j*c**k*t**l for i,j,k,l in result["terms"]), R.zero())
    assert direct == listed and len(result["terms"]) == 24
    symmetric = json.loads(files["symmetric"].read_text())
    e1, e2, e3, e4 = a+b+c+t, a*b+a*c+a*t+b*c+b*t+c*t, a*b*c+a*b*t+a*c*t+b*c*t, a*b*c*t
    symmetric_expansion = sum((e1**i*e2**j*e3**k*e4**l for i,j,k,l in symmetric["terms"]), R.zero())
    assert direct == symmetric_expansion and len(symmetric["terms"]) == 6
    binary = PolynomialRing(GF(2), "T")
    T = binary.gen()
    n41 = json.loads(files["n41_relation"].read_text())
    n41_points = [item["raw_pair_point"] for item in n41["source_pair_states"][:3]]
    n41_audit = group_control(41, T**41+T**3+1, n41_points)
    n131 = json.loads(files["n131_control"].read_text())["solutions"][0]
    leaves = n131["raw_leaves"]
    field131 = GF(2**131, "T", modulus=T**131+T**13+T**2+T+1)
    curve131 = EllipticCurve(field131, [1, 0, 0, 0, 1])
    pairs = []
    for index in range(0, 6, 2):
        left = curve131(*(decode(field131, value, 131) for value in leaves[index]))
        right = curve131(*(decode(field131, value, 131) for value in leaves[index+1]))
        pairs.append(left+right)
    n131_audit = group_control(131, T**131+T**13+T**2+T+1,
                                [[encode(point[0]),encode(point[1])] for point in pairs])
    audit = {"status": "PASS_SYMBOLIC_RESULTANT_AND_GROUP_CONTROLS",
             "protocol_sha256": sha(HERE / "audit_protocol.json"),
             "term_count": len(result["terms"]),
             "symmetric_term_count": len(symmetric["terms"]),
             "n41": n41_audit, "n131": n131_audit}
    (HERE / "audit_result.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": audit["status"], "term_count": audit["term_count"],
                      "n41_roots": len(n41_audit["field_roots"]),
                      "n131_roots": len(n131_audit["field_roots"])}, sort_keys=True))


if __name__ == "__main__":
    main()
