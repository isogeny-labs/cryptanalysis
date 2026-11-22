"""Exact W23 product rank and independent sample-edge Sage replay.

W23 mask words encode w=u^2+u, unlike the N41 W8 mask words encoding u.
"""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing


D = Path(__file__).resolve().parent
ROOT = D.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    p = read(D / "n131_leaf_projection_protocol_v3.json")
    assert sha(D / "n131_leaf_projection_v3_sage.py") == p["runner_sha256"]
    for relative, digest in p["sources"].items():
        assert sha(ROOT / relative) == digest, relative
    census = read(ROOT / "n131_w23_sixpair_density_20261016/run_result.json")
    worker = census["worker_result"]
    assert worker["usable_edges"] == 1049218
    seed_mask = worker["seed_mask"]
    assert seed_mask == 898618
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    modulus = t**131 + t**13 + t**2 + t + 1
    assert modulus.is_irreducible()
    field = GF(2**131, name="t", modulus=modulus)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    def w_of_mask(mask):
        return field(sum((t**(i + 1) for i in range(23) if mask >> i & 1), ring(0)))
    def bits(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
    seed = w_of_mask(seed_mask)
    assert seed not in (0, 1)
    def halftrace(value):
        original = value
        result = field(0)
        for _ in range(66):
            result += value
            value = value**4
        assert result**2 + result == original
        return result
    seed_u = halftrace(seed)
    assert seed_u not in (0, 1)
    def product(w):
        return w * (w + seed)
    bit_positions = [i for i in range(23) if i != seed_mask.bit_length() - 1]
    basis_products = [product(w_of_mask(1 << i)) for i in bit_positions]
    vectors = [bits(x) for x in basis_products]
    pivots = {}
    def insert(value):
        while value:
            k = value.bit_length() - 1
            if k in pivots:
                value ^= pivots[k]
            else:
                pivots[k] = value
                return True
        return False
    assert all(insert(x) for x in vectors)
    assert len(pivots) == 22
    product_one_in_span = not insert(1)
    assert not product_one_in_span
    sample = worker["sample_edges"]
    assert len(sample) == 8
    checked_sums = 0
    for a_mask, b_mask, _, _ in sample:
        assert a_mask ^ b_mask == seed_mask
        a, b = w_of_mask(a_mask), w_of_mask(b_mask)
        assert a not in (0, 1) and b not in (0, 1)
        assert a.trace() == b.trace() == 0
        assert (1/a).trace() == (1/b).trace() == 0
        xa, xb = 1/halftrace(a) + 1, 1/halftrace(b) + 1
        lifts_a = curve.lift_x(xa, all=True)
        lifts_b = curve.lift_x(xb, all=True)
        assert len(lifts_a) == len(lifts_b) == 2
        prod = product(a)
        code = sum(((a_mask >> bit) & 1) << j
                   for j, bit in enumerate(bit_positions))
        predicted = sum((basis_products[j] for j in range(22) if code >> j & 1), field(0))
        assert prod == predicted
        roots = set()
        for pa in lifts_a:
            for pb in lifts_b:
                total = pa + pb
                assert total != curve(0) and total[0] != 0
                c = 1 / total[0]
                assert c not in (0, 1)
                assert prod*c + (((seed_u + 1)*c + seed_u)**2) == 0
                roots.add(bits(c))
                checked_sums += 1
        assert len(roots) == 2
    assert checked_sums == 32
    result = {"status": "PASS_N131_W23_DIRECT_LEAF_PROJECTION",
              "protocol_sha256": sha(D / "n131_leaf_projection_protocol_v3.json"),
              "field_modulus_irreducible": True,
              "fixed_seed_mask": seed_mask,
              "seed_model": "w=u^2+u; pair leaf uses u=halftrace(w)",
              "product_map_rank": 22,
              "product_one_in_span": product_one_in_span,
              "predicted_direct_leaf_and_gates_per_slot": 22 * 131,
              "sample_edges": len(sample),
              "independent_signed_pair_sums": checked_sums,
              "two_roots_per_sample_edge": True}
    (D / "n131_leaf_projection_v3_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
