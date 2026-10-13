"""Inspect actual pair and total coordinate charts for the fixed four masks."""

import json
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial()))


def decode(field, value):
    return sum((field.gen() ** i for i in range(41) if value >> i & 1), field.zero())


def main():
    poly = PolynomialRing(GF(2), "T")
    T = poly.gen()
    field = GF(2**41, "T", modulus=T**41 + T**3 + 1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    targets = json.loads((HERE / "join_stdout.log").read_text())["cases"]["constructed"]
    masks = [22, 63, 8, 21]
    choices = [curve.lift_x(decode(field, mask << 1), all=True) for mask in masks]
    out = []
    for i in range(2):
        for j in range(2):
            p = choices[0][i] + choices[1][j]
            out.append({"pair": [masks[0], masks[1]], "signs": [i, j],
                        "x": encode(p[0]), "inverse_x": encode(1 / p[0]),
                        "inverse_x_plus_one": encode(1 / (p[0] + 1))})
    for i in range(2):
        for j in range(2):
            p = choices[2][i] + choices[3][j]
            out.append({"pair": [masks[2], masks[3]], "signs": [i, j],
                        "x": encode(p[0]), "inverse_x": encode(1 / p[0]),
                        "inverse_x_plus_one": encode(1 / (p[0] + 1))})
    result = {"expected_pair_reciprocals": targets["first_exact"],
              "expected_target_reciprocal": targets["target_reciprocal"],
              "actual_pairs": out}
    (HERE / "diagnose_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
