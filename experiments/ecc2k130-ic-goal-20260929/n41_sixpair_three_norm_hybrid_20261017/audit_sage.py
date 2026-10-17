"""Independent Sage curve, quadratic-source, and three-norm replay."""
import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

D = Path(__file__).resolve().parent
ROOT = D.parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
protocol = json.loads((D / "audit_protocol.json").read_text())
for path, digest in protocol["sources"].items():
    assert sha(path) == digest, path
geometry = json.loads((ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json").read_text())
hit = json.loads((ROOT / "n41_sixpair_shared_target_20261017/join_audit_result.json").read_text())
build = json.loads((D / "build_result.json").read_text())
R = PolynomialRing(GF(2), "t")
t = R.gen()
F = GF(2**41, name="t", modulus=t**41+t**3+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(41)]))


def point(raw):
    x, y = map(dec, raw)
    assert E.is_on_curve(x, y)
    return E(x, y)


def f4(a, b, c, u):
    aa, bb, cc, uu = a**2, b**2, c**2, u**2
    A, B, C = 1 + aa*bb, a*b, aa + bb
    V, W, H = 1 + cc*uu, c*u, cc + uu
    return (A*H+C*V)**2 + (A*W+B*V)*(B*H+C*W)


source = [point(row["raw_sum"]) for row in hit["pair_rows"]]
target = point(hit["raw_target"])
assert sum(source, E(0)) == target
left = sum(source[:3], E(0))
right = sum(source[3:], E(0))
assert left != E(0) and right != E(0)
assert left + right == target
left_reciprocal = 1 / left[0]
right_reciprocal = 1 / right[0]
target_reciprocal = 1 / target[0]

seed_s = dec(geometry["blocks"][0]["s"])
seed = seed_s**2 + seed_s
halftrace = sum((seed**(2**(2*j)) for j in range(21)), F.zero())
assert halftrace**2 + halftrace == seed
h2 = halftrace**2
bits = [i for i in range(8) if i != geometry["fixed_seed_sum_code"].bit_length()-1]
quadratic_checks = 0
root_sets = []
for slot in range(3):
    rotation = geometry["rotations"][slot]
    row = hit["pair_rows"][slot]
    code = row["masks"][0]
    product = sum((dec(geometry["blocks"][0]["product_basis"][bit])
                   for bit in bits if code >> bit & 1), F.zero())
    hs = h2**(2**rotation)
    leading = 1 + hs
    assert leading != 0
    alpha = product**(2**rotation) / leading
    beta = hs / leading
    states = [state for state in geometry["blocks"][slot]["states"] if state["a"] == code]
    assert len(states) == 4
    roots = sorted({1 / dec(state["raw_sum"][0]) for state in states},
                   key=lambda x: sum(int(bit) << i for i, bit in
                                     enumerate(x.polynomial().list())))
    assert len(roots) == 2
    for root in roots:
        assert root**2 + alpha*root + beta == 0
        quadratic_checks += 1
    root_sets.append(roots)
assert left_reciprocal in {1 / sum(combo, E(0))[0]
                           for combo in itertools.product(*[
                               [point(state["raw_sum"]) for state in geometry["blocks"][slot]["states"]
                                if state["a"] == hit["pair_rows"][slot]["masks"][0]]
                               for slot in range(3)])
                           if sum(combo, E(0)) != E(0)}
norm_product = F.one()
for roots in itertools.product(*root_sets):
    norm_product *= f4(*roots, left_reciprocal)
assert norm_product == 0
assert (1 + (left_reciprocal*right_reciprocal)**2)*target_reciprocal**2 + \
       left_reciprocal*right_reciprocal*target_reciprocal + \
       left_reciprocal**2 + right_reciprocal**2 == 0
assert build["public_raw_point"] == hit["raw_target"]
out = {"status": "PASS_INDEPENDENT_SAGE_THREE_NORM_HYBRID_CONTROL",
       "protocol_sha256": sha(D / "audit_protocol.json"),
       "build_sha256": sha(D / "build_result.json"),
       "source_quadratic_roots_checked": quadratic_checks,
       "left_norm_product_zero": True,
       "six_pair_sum_matches_target": True}
(D / "audit_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(out["status"], flush=True)
