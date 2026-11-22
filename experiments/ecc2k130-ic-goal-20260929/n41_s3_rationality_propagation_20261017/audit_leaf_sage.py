"""Independent Sage census of every fixed-seed leaf root and pair sum."""
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
    p = read(D / "audit_protocol.json")
    assert sha(D / "audit_leaf_sage.py") == p["auditor_sha256"]
    for relative, digest in p["sources"].items():
        assert sha(ROOT / relative) == digest, relative
    g = read(ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json")
    source = read(ROOT / "n41_w7_entropy_cubic_20261011/w8/geometry.json")
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, name="t", modulus=t**41 + t**3 + 1)
    assert (t**41 + t**3 + 1).is_irreducible()
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    def dec(word):
        return field(ring([(int(word) >> i) & 1 for i in range(41)]))
    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
    def xy(point):
        return [enc(point[0]), enc(point[1])]
    rows = {row["mask"]: row for row in source["rows"]}
    basis = [dec(x) for x in g["blocks"][0]["basis"]]
    seed_mask = g["fixed_seed_sum_code"]
    seed = sum((basis[i] for i in range(8) if seed_mask >> i & 1), field(0))
    assert enc(seed) == g["blocks"][0]["s"] and seed != field(1)
    bits = [i for i in range(8) if i != seed_mask.bit_length() - 1]
    assert len(bits) == 7
    code_count = state_count = root_count = 0
    for slot in range(6):
        rotation = g["rotations"][slot]
        by_code = {}
        for state in g["blocks"][slot]["states"]:
            a, b = state["a"], state["b"]
            assert b == a ^ seed_mask
            code = sum(((a >> bit) & 1) << j for j, bit in enumerate(bits))
            by_code.setdefault(code, []).append(state)
            signed = []
            for mask, sign in ((a, state["sign_a"]), (b, state["sign_b"])):
                point = curve(*map(dec, rows[mask]["raw_point"]))
                signed.append(-point if sign else point)
            total = signed[0] + signed[1]
            assert total != curve(0) and total[0] not in (0, 1)
            rotated = curve(total[0] ** (1 << rotation), total[1] ** (1 << rotation))
            assert xy(rotated) == state["raw_sum"]
            state_count += 1
        assert len(by_code) == 40
        for code, states in by_code.items():
            assert len(states) == 4
            a = states[0]["a"]
            source_a = sum((basis[i] for i in range(8) if a >> i & 1), field(0))
            source_b = source_a + seed
            product = (source_a**2 + source_a) * (source_b**2 + source_b)
            direct = sum((dec(g["blocks"][0]["product_basis"][bit])
                          for j, bit in enumerate(bits) if code >> j & 1), field(0))
            assert product == direct
            roots = set()
            for state in states:
                x = dec(state["raw_sum"][0]) ** (1 << (41 - rotation))
                c = 1 / x
                assert c not in (0, 1)
                assert product*c + (((seed + 1)*c + seed)**2) == 0
                roots.add(enc(c))
            assert len(roots) == 2
            assert (seed + 1)**2 != 0  # Leading coefficient of the quadratic.
            # Two distinct roots exhaust a nonzero quadratic over this field.
            code_count += 1
            root_count += len(roots)
    assert (state_count, code_count, root_count) == (960, 240, 480)
    result = {"status": "PASS_INDEPENDENT_S3_LEAF_SUPPORT",
              "audit_protocol_sha256": sha(D / "audit_protocol.json"),
              "curve_id": g["curve_id"],
              "curve_states_replayed": state_count,
              "code_slot_quadratics": code_count,
              "distinct_expected_roots_across_code_slots": root_count,
              "roots_per_quadratic": 2,
              "field_modulus_irreducible": True,
              "leading_coefficient_nonzero": True}
    (D / "leaf_audit_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
