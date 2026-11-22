"""Transform the frozen N131 public target and all four raw preimages."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, Zmod

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
INPUT = GOAL / "n131_fixed_seed_eight_pair_circuit_20261010/target_preimages.json"
ORDER = 680564733841876926932320129493409985129


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "n131_projection_protocol.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_N131_TARGET_PROJECTION"
    assert protocol["sha256"] == {
        "source": sha(HERE / "project_n131_sage.py"),
        "public_preimages": sha(INPUT),
        "sage_runtime": sha(HERE / "n131_sage_runtime_info.json")}
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    def dec(n):
        return field(ring([(n >> i) & 1 for i in range(131)]))
    def enc(a):
        return sum(int(bit) << i for i, bit in enumerate(a.polynomial().list()))
    def xy(point):
        return [enc(point[0]), enc(point[1])]
    def frob(point, shift):
        return curve(point[0]**(1 << shift), point[1]**(1 << shift))
    data = json.loads(INPUT.read_text())
    assert data["curve_id"] == protocol["curve_id"]
    target = curve(*map(dec, data["public_target"]))
    assert ORDER*target == curve(0)
    raw = [curve(*map(dec, row["point"])) for row in data["preimages"]]
    assert len(raw) == len(set(raw)) == 4
    assert all(4*point == target for point in raw)
    poly = PolynomialRing(Zmod(ORDER), "L")
    L = poly.gen()
    roots = [int(value) for value, _ in (L*L+L+2).roots()]
    chosen = [lam for lam in roots if lam*target == frob(target, 1)]
    assert len(roots) == 2 and len(chosen) == 1
    lam = chosen[0]
    shift = protocol["frobenius_shift"]
    factor = (1+pow(lam, shift, ORDER)) % ORDER
    assert factor
    inverse = pow(factor, -1, ORDER)
    inverse_odd = inverse if inverse % 2 else inverse+ORDER
    assert inverse_odd % 2 == 1 and inverse_odd % ORDER == inverse
    transformed = inverse*target
    assert factor*transformed == target
    assert transformed+frob(transformed, shift) == target
    preimages = [inverse_odd*point for point in raw]
    assert len(set(preimages)) == 4
    assert all(4*point == transformed and point != curve(0) and point[0] != 0
               for point in preimages)
    result = {"status": "PASS_CHECKED_SAGE_N131_COMMON_FACTOR_TARGET",
              "curve_id": protocol["curve_id"], "public_point": xy(target),
              "transformed_target": xy(transformed),
              "raw_preimages": [xy(point) for point in preimages],
              "raw_preimage_reciprocals": [enc(1/point[0]) for point in preimages],
              "frobenius_shift": shift, "lambda_mod_r": lam,
              "factor_mod_r": factor, "inverse_mod_r": inverse,
              "odd_raw_preimage_multiplier": inverse_odd,
              "subgroup_order": ORDER, "protocol_sha256": sha(HERE / "n131_projection_protocol.json")}
    with (HERE / "n131_projection_result.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(result["status"], factor, flush=True)


if __name__ == "__main__":
    main()
