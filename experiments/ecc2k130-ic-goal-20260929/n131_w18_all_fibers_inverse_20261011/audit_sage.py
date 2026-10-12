#!/usr/bin/env sage -python
"""Independently replay all 128 raw-fiber terminal residuals in Sage."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011"
R = 680564733841876926932320129493409985129


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    control = json.loads((HERE / "control_result.json").read_text())
    query = json.loads((HERE / "query_result.json").read_text())
    fixture = json.loads((BASE / "control_fixture.json").read_text())
    runtime = json.loads((HERE / "sage_runtime_info.json").read_text())
    assert runtime["status"] == "verified"
    assert protocol["source_sha256"]["sage_audit"] == sha(Path(__file__))
    assert control["protocol_sha256"] == query["protocol_sha256"] == sha(HERE / "protocol.json")

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

    torsion = [curve(0) if row is None else point(row)
               for row in protocol["four_torsion_offsets"]]
    assert len(set(torsion)) == 4 and all(4 * offset == curve(0) for offset in torsion)
    terminal = [point(row["rotated_raw_point"]) for row in protocol["terminal_pool"]]
    assert len(terminal) == 32 and len(set(terminal)) == 32
    assert all(R * (4 * term) == curve(0) for term in terminal)

    public = point(query["public_target"])
    assert R * public == curve(0)
    canonical = pow(4, -1, R) * public
    assert 4 * canonical == public
    public_preimages = [canonical + offset for offset in torsion]
    fixture_raw = point(fixture["raw_target"])
    control_preimages = [fixture_raw + offset for offset in torsion]
    fixture_public = 4 * fixture_raw
    assert all(4 * row == public for row in public_preimages)
    assert all(4 * row == fixture_public for row in control_preimages)
    assert [encode(fixture_public[0]), encode(fixture_public[1])] == control["fixture_public_point"]

    for preimages, receipt in ((public_preimages, query), (control_preimages, control)):
        assert len(receipt["raw_preimages"]) == 4 and len(receipt["residuals"]) == 128
        for index, raw in enumerate(preimages):
            assert [encode(raw[0]), encode(raw[1])] == receipt["raw_preimages"][index]
            for terminal_index, term in enumerate(terminal):
                residual = raw - term
                recorded = receipt["residuals"][32 * index + terminal_index]
                assert recorded["preimage_index"] == index
                assert recorded["terminal_state_index"] == terminal_index
                assert residual != curve(0) and residual[0] not in (0, 1)
                assert [encode(residual[0]), encode(residual[1])] == recorded["point"]
                assert encode(1 / residual[0]) == recorded["standard_reciprocal"]

    result = {"status": "PASS_INDEPENDENT_SAGE_ALL_128_RESIDUALS",
              "curve_id": protocol["curve_id"],
              "public_target": query["public_target"],
              "public_preimages": 4, "terminal_states": 32,
              "control_residuals": 128, "ordinary_residuals": 128,
              "sha256": {"script": sha(Path(__file__)),
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
