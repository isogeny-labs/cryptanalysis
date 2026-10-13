"""Freeze the subgroup inverse of 1 + Frobenius^7 on the N41 public point."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, Zmod

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SOURCE = GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
FIXTURE = GOAL / "n41_w7_entropy_cubic_20261011/w8/fixture.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "prepare_protocol.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_TARGET_TRANSFORM"
    assert protocol["sha256"] == {
        "source": sha(HERE / "prepare_sage.py"), "pairs": sha(SOURCE),
        "fixture": sha(FIXTURE), "sage_runtime": sha(HERE / "sage_runtime_info.json")}
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, name="t", modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    order = 549756390943
    def dec(n):
        return field(ring([(n >> i) & 1 for i in range(41)]))
    def enc(a):
        return sum(int(bit) << i for i, bit in enumerate(a.polynomial().list()))
    def xy(point):
        return [enc(point[0]), enc(point[1])]
    def frob(point, shift):
        return curve(point[0]**(1 << shift), point[1]**(1 << shift))
    fixture = json.loads(FIXTURE.read_text())
    target = curve(*map(dec, fixture["public_target_transported"]))
    assert xy(target) == protocol["public_point"]
    assert order*target == curve(0)
    sample = None
    source_rows = 0
    with SOURCE.open() as stream:
        assert stream.readline().split() == ["ECC2K41_ALLSEED4", "4", "4"]
        for line in stream:
            row = line.split()
            if row[0] == "S" and row[1] == "0":
                source_rows += 1
                if sample is None:
                    sample = 4*curve(dec(int(row[-2])), dec(int(row[-1])))
    assert source_rows == 30952 and sample != curve(0) and order*sample == curve(0)
    poly = PolynomialRing(Zmod(order), "L")
    L = poly.gen()
    roots = [int(root) for root, _ in (L*L+L+2).roots()]
    selected = [lam for lam in roots if lam*sample == frob(sample, 1)]
    assert len(roots) == 2 and len(selected) == 1
    lam = selected[0]
    shift = protocol["frobenius_shift"]
    factor = (1+pow(lam, shift, order)) % order
    assert factor and factor.bit_length() <= 41
    inverse = pow(factor, -1, order)
    transformed = inverse*target
    assert factor*transformed == target
    assert transformed+frob(transformed, shift) == target
    result = {"status": "PASS_CHECKED_SAGE_TARGET_FACTOR",
              "curve_id": protocol["curve_id"], "public_point": xy(target),
              "transformed_target": xy(transformed), "frobenius_shift": shift,
              "lambda_mod_r": lam, "factor_mod_r": factor,
              "inverse_mod_r": inverse, "subgroup_order": order,
              "source_rows_slot0": source_rows, "sample_projected_point": xy(sample),
              "protocol_sha256": sha(HERE / "prepare_protocol.json")}
    with (HERE / "target.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(result)


if __name__ == "__main__":
    main()
