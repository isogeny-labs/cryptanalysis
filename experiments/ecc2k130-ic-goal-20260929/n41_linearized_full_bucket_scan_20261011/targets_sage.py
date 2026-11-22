"""Derive all raw residual lifts with the checked repository Sage runtime."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
SOURCE = BASE / "n41_symbolic_two_bucket_20261011/protocol.json"
GEOMETRY = BASE / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json"


def decode(field, bits):
    return sum((field.gen()**i for i in range(41) if bits >> i & 1), field.zero())


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial()))


def main():
    prior = json.loads(SOURCE.read_text())
    assert hashlib.sha256(GEOMETRY.read_bytes()).hexdigest() == prior["sha256"]["geometry"]
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, "t", modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    geometry = json.loads(GEOMETRY.read_text())["n41"]
    torsion = curve(field.one(), field.zero())
    inv4 = pow(4, -1, geometry["subgroup_order"])
    rows = []
    for kind in ("positive", "negative"):
        point = curve(*(decode(field, x) for x in prior[kind + "_residual"]))
        for option in range(4):
            raw = inv4*point+option*torsion
            assert 4*raw == point and raw[0] != 1
            rows.append({"kind": kind, "option": option,
                         "raw_xy": [encode(raw[0]), encode(raw[1])],
                         "target_z": encode(1/(raw[0]+1))})
    output = {"source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "geometry_sha256": hashlib.sha256(GEOMETRY.read_bytes()).hexdigest(),
              "rows": rows}
    (HERE / "targets.json").write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"raw_lifts": len(rows), "positive_option_3": rows[3]}))


if __name__ == "__main__":
    main()
