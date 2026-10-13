"""Checked Sage replay of the positive product-family pair."""

import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode(field, value):
    return sum((field.gen() ** i for i in range(41) if value >> i & 1), field.zero())


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial()))


def main():
    protocol = json.loads((HERE / "sage_protocol.json").read_text())
    assert protocol["status"] == "FROZEN"
    assert protocol["source_sha256"] == sha(HERE / "sage_control.py")
    assert protocol["runtime_sha256"] == sha(HERE / "sage_runtime_info.json")
    assert protocol["cases_sha256"] == sha(HERE / "cases.jsonl")
    first = json.loads((HERE / "cases.jsonl").read_text().splitlines()[0])
    assert first["positive"] and first["pivot_hits"] == first["direct_hits"] == 1
    binary = PolynomialRing(GF(2), "T")
    T = binary.gen()
    field = GF(2**41, "T", modulus=T**41 + T**3 + 1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    masks = protocol["masks"]
    choices = [curve.lift_x(decode(field, mask << 1), all=True) for mask in masks]
    assert all(len(points) == 2 for points in choices)
    products = []
    for index in (0, 2):
        p = decode(field, masks[index] << 1) * decode(field, masks[index + 1] << 1)
        code = encode(p) >> 2
        products.append(code)
    assert products == protocol["product_codes"] == [first["left_product"], first["right_product"]]
    hits = []
    target = protocol["target_reciprocal"]
    for signs in itertools.product(range(2), repeat=4):
        points = [choices[i][signs[i]] for i in range(4)]
        left, right = points[0] + points[1], points[2] + points[3]
        total = left + right
        if not left or not right or not total:
            continue
        if encode(1 / total[0]) == target:
            hits.append({"signs": list(signs),
                         "pair_reciprocals": [encode(1 / left[0]), encode(1 / right[0])],
                         "sum_point": [encode(total[0]), encode(total[1])]})
    assert hits
    result = {"status": "PASS_CHECKED_SAGE_POSITIVE_FAMILY_REPLAY",
              "protocol_sha256": sha(HERE / "sage_protocol.json"),
              "product_codes": products, "masks": masks,
              "target_reciprocal": target, "sign_assignments": len(hits),
              "first": hits[0]}
    (HERE / "sage_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
