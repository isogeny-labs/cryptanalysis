"""Checked-Sage replay of every public-x probe and rational pair test."""

import gzip
import hashlib
import json
from math import gcd
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, ZZ


HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "xedni-large-order-admission-20261115" / "result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def point_coords(point):
    return None if point.is_zero() else [int(point[0]), int(point[1])]


def expected_lift(point, p, shifts):
    if point.is_zero():
        return {"status": "identity", "probes": 0}
    xres, yres = int(point[0]), int(point[1])
    x0 = xres if xres <= p // 2 else xres - p
    for index, shift in enumerate(shifts, 1):
        x = ZZ(x0 + shift * p)
        f = x**3 - x - 2
        if f < 0 or not f.is_square():
            continue
        root = f.sqrt()
        for y in (root, -root):
            if int(y % p) == yres:
                rational = EllipticCurve(QQ, [0, 0, 0, -1, -2])(x, y)
                assert int(rational[0]) == int(x) and int(rational[1]) == int(y)
                return {"status": "lifted", "probes": index,
                        "shift": shift, "rational_point": [int(x), int(y)]}
    return {"status": "window_exhausted", "probes": len(shifts)}


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    selection = json.loads(INPUT.read_text())
    assert result["status"] == "PASS"
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["source_sha256"] == sha(HERE / "run.py")
    assert result["input_sha256"] == sha(INPUT) == \
        protocol["input_selection_result_sha256"]
    selected = [item for item in selection["rows"] if item["selected"]]
    assert len(selected) == len(result["fields"])
    shifts = protocol["lift_rule"]["shift_order"]
    family = [(a, b) for a in range(1, 4) for b in range(-3, 4)
              if b != 0 and gcd(a, abs(b)) == 1]
    total_queries = total_probes = total_hits = 0
    for item, summary in zip(selected, result["fields"]):
        p, q = item["field_prime"], item["subgroup_order"]
        curve = EllipticCurve(GF(p), protocol["base_curve_coefficients"])
        assert int(curve.cardinality()) == item["curve_order"]
        P = curve(2, 2)
        order = int(P.order())
        assert order == summary["generator_reduction_order"]
        m = order // q
        assert order == m * q and m == summary["subgroup_multiplier_m"]
        G = m * P
        assert int(G.order()) == q
        Q = 17 * G
        path = HERE / summary["rows_path"]
        assert sha(path) == summary["rows_sha256"]
        with gzip.open(path, "rt") as stream:
            rows = [json.loads(line) for line in stream]
        assert len(rows) == q
        lifts = []
        probes = 0
        for t, row in enumerate(rows):
            reduced = Q - t * G
            assert row["t"] == t and row["reduced_point"] == point_coords(reduced)
            expected = expected_lift(reduced, p, shifts)
            assert {k: v for k, v in row.items() if k not in ("t", "reduced_point")} == expected
            probes += row["probes"]
            if row["status"] == "lifted":
                lifts.append(row)
                x, y = row["rational_point"]
                assert curve(x, y) == reduced
        assert probes == summary["candidate_x_probes"]
        assert len(lifts) == summary["point_lifts"]
        assert q - 1 - len(lifts) == summary["failed_point_lifts"]
        assert summary["identity_queries"] == 1
        assert summary["ordered_admissible_lifted_pairs"] == len(lifts) * (len(lifts) - 1)
        assert summary["rational_group_tests"] == len(family) * len(lifts) * (len(lifts) - 1)
        rational = EllipticCurve(QQ, protocol["base_curve_coefficients"])
        hits = []
        for first in lifts:
            for second in lifts:
                if first["t"] == second["t"]:
                    continue
                A = rational(*first["rational_point"])
                B = rational(*second["rational_point"])
                for a, b in family:
                    if a * A + b * B != rational(0):
                        continue
                    assert a * curve(*first["reduced_point"]) + \
                        b * curve(*second["reduced_point"]) == curve(0)
                    useful = (a + b) % q != 0
                    scalar = ((a * first["t"] + b * second["t"]) *
                              pow(a + b, -1, q)) % q if useful else None
                    if useful:
                        assert scalar * G == Q
                    hits.append({"t1": first["t"], "t2": second["t"],
                                 "coefficients": [a, b], "useful": useful,
                                 "recovered_scalar": scalar})
        assert hits == summary["rational_relation_hits"]
        total_queries += q
        total_probes += probes
        total_hits += len(hits)
    assert total_queries == result["totals"]["queries"]
    assert total_probes == result["totals"]["candidate_x_probes"]
    assert total_hits == result["total_rational_relation_hits"]
    print(json.dumps({"schema": "xedni-public-coordinate-lift-audit-v1",
                      "status": "PASS", "fields": len(selected),
                      "queries": total_queries, "candidate_x_probes": total_probes,
                      "rational_relation_hits": total_hits}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
