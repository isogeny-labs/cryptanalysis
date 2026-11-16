"""Frozen public-coordinate denominator search and rational relation census."""

import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from fractions import Fraction
from math import gcd, isqrt
from pathlib import Path


HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "xedni-large-order-admission-20261115" / "result.json"
PARENT_RESULT = HERE.parent / "xedni-public-coordinate-lift-20261115" / "result.json"
PARENT_SOURCE = HERE.parent / "xedni-public-coordinate-lift-20261115" / "run.py"
spec = importlib.util.spec_from_file_location("xedni_integer_window", PARENT_SOURCE)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shifts(limit):
    return [0] + [value for k in range(1, limit + 1) for value in (-k, k)]


def lift(point, p, dmax, shift_order):
    if point is None:
        return {"status": "identity", "probes": 0}
    xres, yres = point
    probes = 0
    for d in range(1, dmax + 1):
        d2, d3 = d * d, d * d * d
        a0 = (xres * d2) % p
        if a0 > p // 2:
            a0 -= p
        for shift in shift_order:
            probes += 1
            a = a0 + shift * p
            if gcd(abs(a), d) != 1:
                continue
            f = a**3 - a * d**4 - 2 * d**6
            if f < 0:
                continue
            b0 = isqrt(f)
            if b0 * b0 != f:
                continue
            for b in (b0, -b0):
                if b % p == (yres * d3) % p:
                    return {"status": "lifted", "probes": probes,
                            "denominator": d, "shift": shift,
                            "rational_representation": [a, d, b]}
    return {"status": "window_exhausted", "probes": probes}


def rational_point(row):
    a, d, b = row["rational_representation"]
    return Fraction(a, d * d), Fraction(b, d * d * d)


def run_field(item, protocol, old):
    p, q = item["field_prime"], item["subgroup_order"]
    P = (2 % p, 2 % p)
    order = parent.point_order(P, p, item["curve_order"])
    assert order % q == 0
    m = order // q
    G = parent.mul(m, P, p)
    assert parent.mul(q, G, p) is None and G is not None
    Q = parent.mul(17, G, p)
    dmax = protocol["lift_rule"]["denominator_range_inclusive"][1]
    shift_order = shifts(protocol["lift_rule"]["shift_abs_limit"])
    assert dmax * len(shift_order) == protocol["lift_rule"]["max_point_probes"]
    rows = []
    for t in range(q):
        R = parent.add(Q, parent.mul(-t, G, p), p)
        point = list(R) if R is not None else None
        attempt = lift(point, p, dmax, shift_order)
        rows.append({"t": t, "reduced_point": point, **attempt})
    path = HERE / "rows" / f"p{p}.jsonl.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as out:
            for row in rows:
                out.write((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode())
    lifted = [row for row in rows if row["status"] == "lifted"]
    hits = []
    for first in lifted:
        for second in lifted:
            if first["t"] == second["t"]:
                continue
            A, B = rational_point(first), rational_point(second)
            for a, b in parent.family():
                if parent.rational_add(parent.rational_mul(a, A),
                                       parent.rational_mul(b, B)) is not None:
                    continue
                assert parent.add(parent.mul(a, tuple(first["reduced_point"]), p),
                                  parent.mul(b, tuple(second["reduced_point"]), p),
                                  p) is None
                useful = (a + b) % q != 0
                recovered = ((a * first["t"] + b * second["t"]) *
                             pow(a + b, -1, q)) % q if useful else None
                if useful:
                    assert recovered == 17
                hits.append({"t1": first["t"], "t2": second["t"],
                             "coefficients": [a, b], "useful": useful,
                             "recovered_scalar": recovered})
    hist = Counter(row["denominator"] for row in lifted)
    assert len(lifted) >= old["point_lifts"]
    return {"field_prime": p, "subgroup_order": q,
            "generator_reduction_order": order, "subgroup_multiplier_m": m,
            "queries": q, "identity_queries": 1,
            "point_lifts": len(lifted), "failed_point_lifts": q - 1 - len(lifted),
            "denominator_histogram": {str(k): hist[k] for k in sorted(hist)},
            "candidate_pairs_probed": sum(row["probes"] for row in rows),
            "parent_integer_window_point_lifts": old["point_lifts"],
            "parent_integer_window_probes": old["candidate_x_probes"],
            "ordered_admissible_lifted_pairs": len(lifted) * (len(lifted) - 1),
            "rational_group_tests": len(parent.family()) * len(lifted) * (len(lifted) - 1),
            "rational_relation_hits": hits,
            "rows_path": str(path.relative_to(HERE)), "rows_sha256": sha(path)}


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["schema"] == "xedni-denominator-lift-protocol-v1"
    assert sha(INPUT) == protocol["input_selection_result_sha256"]
    assert sha(PARENT_RESULT) == protocol["parent_integer_window_result_sha256"]
    assert sha(PARENT_SOURCE) == protocol["parent_arithmetic_source_sha256"]
    selected = [x for x in json.loads(INPUT.read_text())["rows"] if x["selected"]]
    old = json.loads(PARENT_RESULT.read_text())["fields"]
    assert [x["field_prime"] for x in selected] == [x["field_prime"] for x in old]
    fields = [run_field(item, protocol, old_field)
              for item, old_field in zip(selected, old)]
    result = {"schema": "xedni-denominator-lift-result-v1",
              "status": "PASS", "protocol_sha256": sha(HERE / "protocol.json"),
              "source_sha256": sha(Path(__file__)),
              "input_sha256": sha(INPUT), "parent_result_sha256": sha(PARENT_RESULT),
              "parent_source_sha256": sha(PARENT_SOURCE),
              "fields": fields,
              "totals": {key: sum(f[key] for f in fields) for key in (
                  "queries", "identity_queries", "point_lifts", "failed_point_lifts",
                  "candidate_pairs_probed", "ordered_admissible_lifted_pairs",
                  "rational_group_tests")},
              "total_rational_relation_hits": sum(len(f["rational_relation_hits"])
                                                  for f in fields)}
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
