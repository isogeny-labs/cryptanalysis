"""Checked-Sage independent replay of denominator probes and relations."""

import gzip
import hashlib
import json
from collections import Counter
from math import gcd
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, ZZ


HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "xedni-large-order-admission-20261115" / "result.json"
PARENT_RESULT = HERE.parent / "xedni-public-coordinate-lift-20261115" / "result.json"
PARENT_SOURCE = HERE.parent / "xedni-public-coordinate-lift-20261115" / "run.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def coordinates(point):
    return None if point.is_zero() else [int(point[0]), int(point[1])]


def search(point, p, curve, dmax, shift_max):
    if point.is_zero():
        return {"status": "identity", "probes": 0}
    xr, yr = int(point[0]), int(point[1])
    probes = 0
    for d in range(1, dmax + 1):
        d2, d3 = d * d, d * d * d
        a0 = (xr * d2) % p
        if a0 > p // 2:
            a0 -= p
        for shift in [0] + [v for k in range(1, shift_max + 1) for v in (-k, k)]:
            probes += 1
            a = ZZ(a0 + shift * p)
            if gcd(abs(int(a)), d) != 1:
                continue
            value = a**3 - a * d**4 - 2 * d**6
            if value < 0 or not value.is_square():
                continue
            root = value.sqrt()
            for b in (root, -root):
                if int(b % p) != (yr * d3) % p:
                    continue
                xq, yq = QQ(a) / d2, QQ(b) / d3
                rational_point = curve(xq, yq)
                assert rational_point[0] == xq and rational_point[1] == yq
                return {"status": "lifted", "probes": probes,
                        "denominator": d, "shift": shift,
                        "rational_representation": [int(a), d, int(b)]}
    return {"status": "window_exhausted", "probes": probes}


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    selection = json.loads(INPUT.read_text())
    old = json.loads(PARENT_RESULT.read_text())
    assert result["status"] == "PASS"
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["source_sha256"] == sha(HERE / "run.py")
    assert result["input_sha256"] == sha(INPUT) == \
        protocol["input_selection_result_sha256"]
    assert result["parent_result_sha256"] == sha(PARENT_RESULT) == \
        protocol["parent_integer_window_result_sha256"]
    assert result["parent_source_sha256"] == sha(PARENT_SOURCE) == \
        protocol["parent_arithmetic_source_sha256"]
    selected = [r for r in selection["rows"] if r["selected"]]
    assert len(selected) == len(old["fields"]) == len(result["fields"])
    arity = [(a, b) for a in range(1, 4) for b in range(-3, 4)
             if b and gcd(a, abs(b)) == 1]
    curve = EllipticCurve(QQ, protocol["base_curve_coefficients"])
    dmax = protocol["lift_rule"]["denominator_range_inclusive"][1]
    shift_max = protocol["lift_rule"]["shift_abs_limit"]
    totals = Counter()
    for item, field, parent_field in zip(selected, result["fields"], old["fields"]):
        p, q = item["field_prime"], item["subgroup_order"]
        reduced_curve = EllipticCurve(GF(p), protocol["base_curve_coefficients"])
        assert int(reduced_curve.cardinality()) == item["curve_order"]
        P = reduced_curve(2, 2)
        order = int(P.order())
        assert order == field["generator_reduction_order"]
        m = order // q
        assert order == m * q == field["subgroup_multiplier_m"] * q
        G = m * P
        assert int(G.order()) == q
        Q = 17 * G
        path = HERE / field["rows_path"]
        assert sha(path) == field["rows_sha256"]
        with gzip.open(path, "rt") as stream:
            rows = [json.loads(line) for line in stream]
        assert len(rows) == q
        lifts = []
        probes = 0
        for t, row in enumerate(rows):
            reduced = Q - t * G
            assert row["t"] == t and row["reduced_point"] == coordinates(reduced)
            expected = search(reduced, p, curve, dmax, shift_max)
            assert {k: v for k, v in row.items() if k not in ("t", "reduced_point")} == expected
            probes += row["probes"]
            if row["status"] == "lifted":
                lifts.append(row)
                a, d, b = row["rational_representation"]
                rational_point = curve(QQ(a) / d**2, QQ(b) / d**3)
                assert reduced_curve(rational_point[0], rational_point[1]) == reduced
        assert probes == field["candidate_pairs_probed"]
        assert len(lifts) == field["point_lifts"]
        assert q - 1 - len(lifts) == field["failed_point_lifts"]
        assert field["identity_queries"] == 1
        assert field["parent_integer_window_point_lifts"] == parent_field["point_lifts"]
        assert field["parent_integer_window_probes"] == parent_field["candidate_x_probes"]
        hist = Counter(str(row["denominator"]) for row in lifts)
        assert dict(hist) == field["denominator_histogram"]
        assert field["ordered_admissible_lifted_pairs"] == len(lifts) * (len(lifts) - 1)
        assert field["rational_group_tests"] == len(arity) * len(lifts) * (len(lifts) - 1)
        hits = []
        for first in lifts:
            for second in lifts:
                if first["t"] == second["t"]:
                    continue
                a1, d1, b1 = first["rational_representation"]
                a2, d2, b2 = second["rational_representation"]
                A = curve(QQ(a1) / d1**2, QQ(b1) / d1**3)
                B = curve(QQ(a2) / d2**2, QQ(b2) / d2**3)
                for a, b in arity:
                    if a * A + b * B != curve(0):
                        continue
                    assert a * reduced_curve(*first["reduced_point"]) + \
                        b * reduced_curve(*second["reduced_point"]) == reduced_curve(0)
                    useful = (a + b) % q != 0
                    scalar = ((a * first["t"] + b * second["t"]) *
                              pow(a + b, -1, q)) % q if useful else None
                    if useful:
                        assert scalar * G == Q
                    hits.append({"t1": first["t"], "t2": second["t"],
                                 "coefficients": [a, b], "useful": useful,
                                 "recovered_scalar": scalar})
        assert hits == field["rational_relation_hits"]
        for key in ("queries", "identity_queries", "point_lifts", "failed_point_lifts",
                    "candidate_pairs_probed", "ordered_admissible_lifted_pairs",
                    "rational_group_tests"):
            totals[key] += field[key]
        totals["rational_relation_hits"] += len(hits)
    assert all(totals[key] == result["totals"][key] for key in result["totals"])
    assert totals["rational_relation_hits"] == result["total_rational_relation_hits"]
    print(json.dumps({"schema": "xedni-denominator-lift-audit-v1", "status": "PASS",
                      "fields": len(selected), "totals": dict(sorted(totals.items()))},
                     sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
