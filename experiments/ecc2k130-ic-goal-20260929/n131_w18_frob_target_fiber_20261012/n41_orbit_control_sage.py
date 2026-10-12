#!/usr/bin/env sage -python
"""Transport an independently replayed ordinary N41 relation through Frobenius."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CONTROL = ROOT / "n41_w8_terminal1_sevenpair_20261012"
GEOMETRY = ROOT / "n41_w7_entropy_cubic_20261011" / "w8" / "fixture.json"
R = 549756390943


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    audit = json.loads((CONTROL / "sage_audit_result_v2.json").read_text())
    fixture = json.loads(GEOMETRY.read_text())
    runtime = json.loads((HERE / "sage_runtime_info.json").read_text())
    assert runtime["status"] == "verified"
    assert audit["status"] == "PASS_INDEPENDENT_N41_TERMINAL4_RELATION"
    assert audit["verified_hits"] == audit["rank_from_empty_matrix"] == 1
    row = audit["replayed"][0]
    assert row["folded_columns_distinct"] == 14
    assert len({term["column"] for term in row["relation_row"]}) == 14
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, name="t", modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def dec(value):
        return field(ring([(int(value) >> bit) & 1 for bit in range(41)]))

    def point(xy):
        return curve([dec(xy[0]), dec(xy[1])])

    def tau(point_value):
        return curve([point_value[0]**2, point_value[1]**2])

    def tau_power(point_value, count):
        for _ in range(count):
            point_value = tau(point_value)
        return point_value

    raw = point(fixture["raw_target_preimages"][0])
    public = point(fixture["public_target_transported"])
    pairs = [point(item["pair_rotated"]) for item in row["source_pairs"]]
    assert len(pairs) == 7 and sum(pairs, curve(0)) == raw
    assert 4 * raw == public and R * public == curve(0)
    lam = int(audit["frobenius_eigenvalue_mod_r"])
    assert pow(lam, 41, R) == 1 and lam != 1
    assert all(tau(4 * pair) == lam * (4 * pair) for pair in pairs)
    assert tau(public) == lam * public
    orbit = []
    for exponent in range(41):
        rotated_pairs = [tau_power(pair, exponent) for pair in pairs]
        rotated_raw = tau_power(raw, exponent)
        rotated_public = tau_power(public, exponent)
        assert sum(rotated_pairs, curve(0)) == rotated_raw
        assert 4 * rotated_raw == rotated_public
        assert rotated_public == pow(lam, exponent, R) * public
        pulled_back = [tau_power(pair, (41-exponent) % 41)
                       for pair in rotated_pairs]
        assert sum(pulled_back, curve(0)) == raw
        assert all(a == b for a, b in zip(pulled_back, pairs))
        orbit.append(rotated_public)
    assert len(set(orbit)) == 41 and tau_power(public, 41) == public
    result = {"status": "PASS_N41_FROBENIUS_ORBIT_RELATION_TRANSPORT",
              "curve_id": audit["curve_id"],
              "ordinary_relation_rank": 1,
              "distinct_folded_columns": 14,
              "target_orbit_size": len(orbit),
              "frobenius_eigenvalue_mod_r": str(lam),
              "source_sha256": {"script": sha(Path(__file__)),
                                "prior_relation": sha(CONTROL / "sage_audit_result_v2.json"),
                                "fixture": sha(GEOMETRY),
                                "runtime": sha(HERE / "sage_runtime_info.json")}}
    with (HERE / "n41_orbit_control_result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(result["status"], result["target_orbit_size"])


if __name__ == "__main__":
    main()
