#!/usr/bin/env sage -python
"""Freeze known-scalar N41 targets and all four raw preimages per target."""

import hashlib
import json
import sys
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n41_w8_sixpair_mitm_20261011"
BASE = HERE.parent / "n41_w7_entropy_cubic_20261011/w8"
R = 549756390943
TARGETS = 128


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def paths():
    return {"script": Path(__file__), "runtime": HERE / "sage_runtime_info.json",
            "geometry": BASE / "geometry.json", "fixture": BASE / "fixture.json",
            "prior_input": PRIOR / "join_input.tsv", "prior_audit": PRIOR / "audit_result.json"}


def freeze():
    prior = json.loads((PRIOR / "audit_result.json").read_text())
    assert prior["status"] == "PASS_INDEPENDENT_N41_PUBLIC_SIX_PAIR_RELATION"
    assert json.loads((HERE / "sage_runtime_info.json").read_text())["status"] == "verified"
    record = {"status": "FROZEN_N41_W8_KNOWN_SCALAR_PANEL",
              "curve_id": prior["curve_id"], "subgroup_order": R,
              "generator_rule": "four times the raw point at the least eligible seed-184 edge endpoint",
              "target_law": "SHA256('N41-W8-logprep-20261011:' || decimal index) modulo r, reject zero and repeats",
              "target_count": TARGETS, "raw_preimages_per_target": 4,
              "torsion_rule": "differences from the four independently verified raw preimages of the frozen transported public point",
              "source_sha256": {name: sha(path) for name, path in paths().items()}}
    save(HERE / "panel_protocol.json", record)
    print(record["status"])


def produce():
    protocol = json.loads((HERE / "panel_protocol.json").read_text())
    assert protocol["source_sha256"] == {name: sha(path) for name, path in paths().items()}
    geometry = json.loads((BASE / "geometry.json").read_text())
    fixture = json.loads((BASE / "fixture.json").read_text())
    rows = {int(row["mask"]): row for row in geometry["rows"]}
    edges = [(a, a ^ 184) for a in sorted(rows)
             if a < (a ^ 184) and a ^ 184 in rows
             and rows[a]["column"] != rows[a ^ 184]["column"]]
    assert len(edges) == 35
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, name="t", modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def dec(value):
        return field(ring([(int(value) >> i) & 1 for i in range(41)]))

    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))

    def xy(point):
        return [enc(point[0]), enc(point[1])]

    mask = edges[0][0]
    generator = 4 * curve(*map(dec, rows[mask]["raw_point"]))
    assert generator != curve(0) and R * generator == curve(0)
    prior_raw = [curve(*map(dec, point)) for point in fixture["raw_target_preimages"]]
    torsion = [point - prior_raw[0] for point in prior_raw]
    assert len(set(torsion)) == 4 and all(4 * point == curve(0) for point in torsion)
    inverse_four = pow(4, -1, R)
    scalar_seen = set()
    lines = [f"TARGETS {TARGETS} 4"]
    public_points = []
    for index in range(TARGETS):
        scalar = int.from_bytes(hashlib.sha256(
            f"N41-W8-logprep-20261011:{index}".encode()).digest(), "big") % R
        assert scalar and scalar not in scalar_seen
        scalar_seen.add(scalar)
        public = scalar * generator
        raw0 = (inverse_four * scalar % R) * generator
        assert 4 * raw0 == public
        raw_set = [raw0 + offset for offset in torsion]
        assert len(set(raw_set)) == 4 and all(4 * point == public for point in raw_set)
        public_points.append(xy(public))
        for raw_index, point in enumerate(raw_set):
            lines.append(f"T {index} {raw_index} {scalar} {enc(point[0])} {enc(point[1])}")
    path = HERE / "panel.tsv"
    with path.open("x") as stream:
        stream.write("\n".join(lines) + "\n")
    result = {"status": "PASS_N41_W8_KNOWN_SCALAR_PANEL",
              "curve_id": protocol["curve_id"], "target_count": TARGETS,
              "raw_preimages_per_target": 4,
              "generator_mask": mask, "generator_projected": xy(generator),
              "distinct_public_points": len(set(map(tuple, public_points))),
              "panel_sha256": sha(path), "panel_bytes": path.stat().st_size,
              "protocol_sha256": sha(HERE / "panel_protocol.json")}
    save(HERE / "panel_result.json", result)
    print(result["status"], result["panel_sha256"])


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("freeze", "produce"):
        raise SystemExit("usage: panel_sage.py freeze|produce")
    {"freeze": freeze, "produce": produce}[sys.argv[1]]()
