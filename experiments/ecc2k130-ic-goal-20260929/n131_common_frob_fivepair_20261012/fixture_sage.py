"""Independent complete N131 five-pair nonexceptional chart fixture."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SUPPORT = GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
FACTOR = GOAL / "n41_common_frob_factor_20261012/n131_projection_result.json"
ORDER = 680564733841876926932320129493409985129


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "fixture_protocol.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_CONSTRUCTED_FIVEPAIR_FIXTURE"
    assert protocol["sha256"] == {
        "source": sha(HERE / "fixture_sage.py"), "support": sha(SUPPORT),
        "factor": sha(FACTOR), "sage_runtime": sha(HERE / "sage_runtime_info.json")}
    columns = {int(m): int(c) for m, c in
               (line.split() for line in SUPPORT.read_text().splitlines())}
    assert len(columns) == 131307
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    zero = curve(0)
    def dec(n):
        return field(ring([(n >> i) & 1 for i in range(131)]))
    def enc(a):
        return sum(int(bit) << i for i, bit in enumerate(a.polynomial().list()))
    def xy(point):
        return [enc(point[0]), enc(point[1])]
    def frob(point, shift):
        return curve(point[0]**(1 << shift), point[1]**(1 << shift))
    def halftrace(value):
        result, term = field.zero(), value
        for _ in range(66):
            result += term
            term = term**4
        assert result**2+result == value
        return result
    cache = {}
    def diagonal(mask):
        if mask not in cache:
            w = dec(mask << 1)
            assert w.trace() == 0
            u = halftrace(w)
            assert u != 0
            raw = curve.lift_x(1+1/u, all=True)[0]
            point = raw+frob(raw, 1)
            assert point != zero and point[0] == 1/w
            cache[mask] = point
        return cache[mask]
    distinct = []
    occupied = set()
    for mask in sorted(columns):
        col = columns[mask]
        if col not in occupied:
            distinct.append(mask)
            occupied.add(col)
        if len(distinct) == 96:
            break
    assert len(distinct) == 96
    for start in range(87):
        masks = distinct[start:start+10]
        pairs = [diagonal(masks[2*i])+diagonal(masks[2*i+1]) for i in range(5)]
        if any(point == zero or point[0] == 0 for point in pairs):
            continue
        middle = [pairs[0]+pairs[1], pairs[2]+pairs[3]]
        middle.append(middle[0]+middle[1])
        raw_total = middle[2]+pairs[4]
        if any(point == zero or point[0] == 0 for point in middle+[raw_total]):
            continue
        break
    else:
        raise RuntimeError("no nonexceptional five-pair chart in frozen window")
    public = 4*raw_total
    assert public != zero and ORDER*public == zero
    factored = public+frob(public, 16)
    factor = json.loads(FACTOR.read_text())
    assert factor["status"] == "PASS_CHECKED_SAGE_N131_COMMON_FACTOR_TARGET"
    assert factor["factor_mod_r"]*public == factored
    result = {"status": "PASS_N131_FIVEPAIR_CONSTRUCTED_CHART",
              "curve_id": factor["curve_id"], "selected_window_start": start,
              "masks": [masks[2*i:2*i+2] for i in range(5)],
              "columns": [columns[mask] for mask in masks],
              "sign_bits": [[0,0] for _ in range(5)],
              "pair_points": [xy(point) for point in pairs],
              "pair_reciprocals": [enc(1/point[0]) for point in pairs],
              "middle_points": [xy(point) for point in middle],
              "intermediate_reciprocals": [enc(1/point[0]) for point in middle],
              "raw_target": xy(raw_total), "raw_target_reciprocal": enc(1/raw_total[0]),
              "projected_target": xy(public), "factored_public_target": xy(factored),
              "frobenius_shift": 16, "protocol_sha256": sha(HERE / "fixture_protocol.json")}
    with (HERE / "fixture.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(result["status"], start, flush=True)


if __name__ == "__main__":
    main()
