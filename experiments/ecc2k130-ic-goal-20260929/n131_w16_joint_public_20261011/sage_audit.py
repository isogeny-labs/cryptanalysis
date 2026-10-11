#!/usr/bin/env sage -python
"""Independent Sage replay of published target, 32 prefixes, and 128 fibers."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
JOINT = ROOT / "n131_w16_joint_prefix_20261010"
ORDER = 680564733841876926932320129493409985129


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lift(F, integer):
    out = F.zero()
    t = F.gen()
    index = 0
    while integer:
        if integer & 1:
            out += t**index
        index += 1
        integer >>= 1
    return out


def encode(value):
    return sum(int(coefficient) << index
               for index, coefficient in enumerate(value.polynomial()))


def point(E, pair):
    return E(lift(E.base_ring(), pair[0]), lift(E.base_ring(), pair[1]))


def main():
    assert not (HERE / "sage_audit.json").exists()
    inputs = json.loads((HERE / "inputs.json").read_text())
    protocol = json.loads((HERE / "protocol.json").read_text())
    archived = json.loads((JOINT / "prefixes.json").read_text())
    assert protocol["source_sha256"]["inputs"] == sha(HERE / "inputs.json")
    assert inputs["source_sha256"]["archived_prefixes"] == sha(JOINT / "prefixes.json")
    ring = PolynomialRing(GF(2), "t")
    t0 = ring.gen()
    F = GF(2**131, "t", modulus=t0**131 + t0**13 + t0**2 + t0 + 1)
    E = EllipticCurve(F, [1, 0, 0, 0, 1])
    Q = point(E, inputs["target_q"])
    assert ORDER * Q == E(0)
    assert inputs["target_q"] == protocol["target_q"]
    checked = 0
    for current, prior in zip(inputs["prefixes"], archived["prefixes"]):
        leaves = [point(E, pair) for pair in prior["raw_leaves"]]
        projected = 4 * (leaves[0] + leaves[1])
        assert [encode(projected[0]), encode(projected[1])] == current["projected_sum"]
        P = point(E, current["projected_sum"])
        R = point(E, current["residual_q"])
        assert P + R == Q and ORDER * P == E(0) and ORDER * R == E(0)
        assert current["masks"] == prior["masks"]
        assert current["signs"] == prior["signs"]
        assert current["columns"] == prior["columns"]
        assert current["projected_sum"] == prior["projected_sum"]
        assert len(current["preimages"]) == len(current["target_reciprocals"]) == 4
        for coords, inverse in zip(current["preimages"], current["target_reciprocals"]):
            T = point(E, coords)
            assert 4 * T == R
            assert T[0] != 0 and encode(1 / T[0]) == inverse
            checked += 1
    assert checked == 128
    out = {"status": "PASS_INDEPENDENT_SAGE_W16_PUBLIC_GEOMETRY",
           "curve_id": inputs["curve_id"], "target_q": inputs["target_q"],
           "prefixes": 32, "raw_fibers": checked,
           "inputs_sha256": sha(HERE / "inputs.json"),
           "protocol_sha256": sha(HERE / "protocol.json"),
           "source_sha256": sha(__file__)}
    (HERE / "sage_audit.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out))


if __name__ == "__main__":
    main()
