"""Independent polynomial-field Sage replay of the exact raw class census."""

import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, Matrix, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(items):
    return hashlib.sha256(json.dumps(items, separators=(",", ":")).encode()).hexdigest()


def main():
    p = json.loads((HERE / "audit_protocol.json").read_text())
    for name, value in p["input_sha256"].items():
        assert sha(p["inputs"][name]) == value
    assert sha(__file__) == p["source_sha256"]
    result = json.loads(Path(p["inputs"]["census_result"]).read_text())
    geometry = json.loads(Path(p["inputs"]["geometry"]).read_text())
    started = time.monotonic()
    n = 131
    bitpoly = (1 << 131) | (1 << 13) | (1 << 2) | (1 << 1) | 1
    ring = PolynomialRing(GF(2), "z")
    modulus = ring([bitpoly >> i & 1 for i in range(n + 1)])
    field = GF(2**n, name="z", modulus=modulus)
    zeta = field.multiplicative_generator() ** ((2**n - 1) // 263)
    assert zeta != 1 and zeta**263 == 1
    basis = [zeta**i + zeta**(263-i) for i in range(1, n + 1)]
    assert sum(basis, field(0)) == 1
    inverse = Matrix(GF(2), [b.list() for b in basis]).transpose().inverse()
    dual = [sum(int(bit) << j for j, bit in enumerate(row)) for row in inverse.rows()]

    def decode(mask):
        value = field(0)
        bits = int(mask)
        while bits:
            low = bits & -bits
            value += basis[low.bit_length() - 1]
            bits ^= low
        return value

    def encode(value):
        polybits = sum(int(bit) << i for i, bit in enumerate(value.list()))
        return sum(((polybits & row).bit_count() & 1) << i for i, row in enumerate(dual))

    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    zero = curve(0)
    r = int(p["subgroup_order"])
    t4 = curve(*[decode(v) for v in result["torsion_generator_coordinates"]])
    group4 = [zero, t4, 2*t4, -t4]
    assert len(set(group4)) == 4 and 4*t4 == zero
    assert all(curve(t[0]**2, t[1]**2) == t for t in group4[1:])
    masks = [int(s, 16) for s in geometry["domain"]["basis_coordinate_masks_hex"]]
    rows = []
    for code in range(1, 1 << len(masks)):
        mask = 0
        for j, value in enumerate(masks):
            if (code >> j) & 1:
                mask ^= value
        phi = decode(mask)
        x = 1/phi + 1
        if not curve.is_x_coord(x):
            continue
        raw = curve.lift_x(x)
        source_class = group4.index(r*raw)
        pair = sorted((source_class, (-source_class) % 4))
        image = raw + curve(raw[0]**2, raw[1]**2)
        assert image != zero and image[0] == raw[0] + 1/raw[0]
        image_pair = [2*source_class % 4] * 2
        assert image_pair == sorted((2*c) % 4 for c in pair)
        if code in (1, 16, 64, 128, 256, 512, 1024, 2048, 4096, 8191):
            assert r*image == group4[image_pair[0]]
        rows.append([code, pair, image_pair, encode(image[0])])
        if (code & 63) == 0:
            assert time.monotonic() - started < p["wall_cap_seconds"]
            assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < p["rss_cap_bytes"]
    assert len(rows) == result["source_raw_x_per_position"]
    assert digest([row[3] for row in rows]) == result["raw_image_x_digest"]
    assert digest([row[:3] for row in rows]) == result["ordered_class_pairs_digest"]
    print(json.dumps({
        "kind": "n131_d13_union_raw_class_independent_sage_audit",
        "status": "PASS_ALL_VALID_SELECTORS",
        "protocol_sha256": sha(HERE / "audit_protocol.json"),
        "valid_selectors": len(rows),
        "raw_image_x_digest": result["raw_image_x_digest"],
        "ordered_class_pairs_digest": result["ordered_class_pairs_digest"],
        "elapsed_seconds": time.monotonic() - started,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
