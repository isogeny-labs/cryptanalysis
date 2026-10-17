"""Check every N41 source quadratic and eight three-family norm charts in Sage."""
import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

D = Path(__file__).resolve().parent
ROOT = D.parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
protocol = json.loads((D / "source_audit_protocol.json").read_text())
for path, digest in protocol["sources"].items():
    assert sha(path) == digest, path
geometry = json.loads((ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json").read_text())
R = PolynomialRing(GF(2), "t")
t = R.gen()
F = GF(2**41, name="t", modulus=t**41+t**3+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])
dec = lambda word: F(R([(int(word) >> i) & 1 for i in range(41)]))
enc = lambda value: sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def f4(a, b, c, u):
    A, B, C = 1+(a*b)**2, a*b, a**2+b**2
    V, W, H = 1+(c*u)**2, c*u, c**2+u**2
    return (A*H+C*V)**2 + (A*W+B*V)*(B*H+C*W)


def states(slot, code):
    found = [s for s in geometry["blocks"][slot]["states"] if s["a"] == code]
    assert len(found) == 4
    points = []
    for state in found:
        x, y = map(dec, state["raw_sum"])
        assert E.is_on_curve(x, y)
        points.append(E(x, y))
    return points


seed_s = dec(geometry["blocks"][0]["s"])
seed = seed_s**2 + seed_s
halftrace = sum((seed**(2**(2*j)) for j in range(21)), F.zero())
assert halftrace**2 + halftrace == seed
h2 = halftrace**2
bits = [i for i in range(8) if i != geometry["fixed_seed_sum_code"].bit_length()-1]
root_cache = {}
quadratic_roots = 0
for slot in range(3):
    rotation = geometry["rotations"][slot]
    hs = h2**(2**rotation)
    for code in geometry["permitted_canonical_a"]:
        product = sum((dec(geometry["blocks"][0]["product_basis"][bit])
                       for bit in bits if code >> bit & 1), F.zero())
        leading = 1 + hs
        assert leading != 0
        alpha = product**(2**rotation) / leading
        beta = hs / leading
        roots = {1/p[0] for p in states(slot, code)}
        assert len(roots) == 2
        assert all(root**2 + alpha*root + beta == 0 for root in roots)
        root_cache[slot, code] = tuple(sorted(roots, key=enc))
        quadratic_roots += 2

triples = ((6, 196, 193), (2, 3, 5), (3, 5, 7), (16, 18, 26),
           (29, 64, 74), (76, 81, 90), (92, 94, 95), (131, 132, 135))
records = []
for codes in triples:
    point_sets = [states(slot, code) for slot, code in enumerate(codes)]
    output = set()
    for points in itertools.product(*point_sets):
        total = sum(points, E(0))
        assert total != E(0) and total[0] != 0
        output.add(1 / total[0])
    assert len(output) == 32
    roots = [root_cache[slot, code] for slot, code in enumerate(codes)]
    for value in output:
        product = F.one()
        for choice in itertools.product(*roots):
            product *= f4(*choice, value)
        assert product == 0
    records.append({"codes": list(codes), "signed_state_count": 64,
                    "distinct_reciprocal_outputs": len(output),
                    "output_digest": hashlib.sha256(json.dumps(sorted(map(enc, output))).encode()).hexdigest()})
out = {"status": "PASS_SAGE_ALL_N41_SOURCE_QUADRATICS_AND_EIGHT_NORMS",
       "protocol_sha256": sha(D / "source_audit_protocol.json"),
       "quadratic_roots_checked": quadratic_roots,
       "records": records}
(D / "source_audit_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(out["status"], flush=True)
