#!/usr/bin/env sage -python
"""Independent checked-Sage replay of the 32 terminal states and fibers."""

import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011"
OLD = ROOT / "n131_fixed_seed_eight_pair_circuit_20261010"
R = 680564733841876926932320129493409985129


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    pool = json.loads((HERE / "pool.json").read_text())
    control = json.loads((HERE / "control_result.json").read_text())
    ordinary = json.loads((HERE / "query_result.json").read_text())
    fixture = json.loads((BASE / "control_fixture.json").read_text())
    target = json.loads((OLD / "target_preimages.json").read_text())
    runtime = json.loads((HERE / "sage_runtime_info.json").read_text())
    assert runtime["status"] == "verified"
    assert protocol["source_sha256"]["pool"] == sha(HERE / "pool.json")
    assert control["protocol_sha256"] == ordinary["protocol_sha256"] == sha(HERE / "protocol.json")
    assert len(pool["states"]) == 32
    poly = PolynomialRing(GF(2), "t")
    t = poly.gen()
    field = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def encode(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))

    def decode(integer):
        return sum((field(t**bit) for bit in range(131) if integer >> bit & 1),
                   field.zero())

    def point(pair):
        return curve([decode(value) for value in pair])

    def coordinate(mask):
        return sum((field(t**(bit+1)) for bit in range(18) if mask >> bit & 1),
                   field.zero())

    def halftrace(value):
        result, power = field.zero(), value
        for _ in range(66):
            result += power
            power = power**4
        assert result**2 + result == value
        return result

    control_raw = point(fixture["raw_target"])
    ordinary_raw = point(target["preimages"][0]["point"])
    public = point(target["public_target"])
    assert 4 * ordinary_raw == public and R * public == curve(0)
    old_raw = point(json.loads((OLD / "planted_chain_result.json").read_text())["raw_target"])
    seen = set()
    for index, row in enumerate(pool["states"]):
        lifts = []
        for mask in row["masks"]:
            u = halftrace(coordinate(mask))
            x = 1 + 1/u
            choices = curve.lift_x(x, all=True)
            assert len(choices) == 2
            lifts.append(choices)
        options = set()
        for left, right in itertools.product(*lifts):
            raw = left + right
            rotated = curve(raw[0]**(1 << 128), raw[1]**(1 << 128))
            options.add(rotated)
        assert len(options) == 4
        terminal = point(row["rotated_raw_point"])
        assert terminal in options and terminal not in seen
        seen.add(terminal)
        assert R * (4 * terminal) == curve(0)
        for target_point, receipt in ((control_raw, control), (ordinary_raw, ordinary)):
            residual = target_point - terminal
            recorded = receipt["residuals"][index]
            assert residual != curve(0) and residual[0] not in (0, 1)
            assert [encode(residual[0]), encode(residual[1])] == recorded["point"]
            assert encode(1/residual[0]) == recorded["standard_reciprocal"]
    assert control_raw - point(pool["states"][pool["control_choice_index"]]["rotated_raw_point"]) == old_raw
    assert control["control_choice_index"] == pool["control_choice_index"]
    result = {"status": "PASS_INDEPENDENT_SAGE_TERMINAL_FIBERS",
              "curve_id": protocol["curve_id"],
              "terminal_states": len(seen),
              "control_residuals": len(control["residuals"]),
              "ordinary_residuals": len(ordinary["residuals"]),
              "public_target": target["public_target"],
              "sha256": {"script": sha(Path(__file__)),
                         "pool": sha(HERE / "pool.json"),
                         "protocol": sha(HERE / "protocol.json"),
                         "control": sha(HERE / "control_result.json"),
                         "query": sha(HERE / "query_result.json"),
                         "runtime": sha(HERE / "sage_runtime_info.json")}}
    with (HERE / "sage_audit_result.json").open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(result["status"])


if __name__ == "__main__":
    main()
