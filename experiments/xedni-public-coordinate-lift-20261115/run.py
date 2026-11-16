"""Frozen public-x rational lift window and complete pair relation census."""

import gzip
import hashlib
import json
from math import gcd, isqrt
from pathlib import Path


HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "xedni-large-order-admission-20261115" / "result.json"
O = None


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add(a, b, p):
    if a is O:
        return b
    if b is O:
        return a
    x1, y1 = a
    x2, y2 = b
    if x1 == x2 and (y1 + y2) % p == 0:
        return O
    if a == b:
        slope = ((3 * x1 * x1 - 1) * pow(2 * y1, -1, p)) % p
    else:
        slope = ((y2 - y1) * pow(x2 - x1, -1, p)) % p
    x3 = (slope * slope - x1 - x2) % p
    return x3, (slope * (x1 - x3) - y1) % p


def mul(k, a, p):
    if k < 0:
        return mul(-k, (a[0], -a[1] % p), p)
    result = O
    while k:
        if k & 1:
            result = add(result, a, p)
        a = add(a, a, p)
        k >>= 1
    return result


def point_order(P, p, limit):
    value = O
    for k in range(1, limit + 1):
        value = add(value, P, p)
        if value is O:
            return k
    raise AssertionError("point order exceeded curve order")


def rational_add(a, b):
    from fractions import Fraction
    if a is O:
        return b
    if b is O:
        return a
    x1, y1 = a
    x2, y2 = b
    if x1 == x2 and y1 == -y2:
        return O
    slope = (Fraction(3 * x1 * x1 - 1) / (2 * y1) if a == b
             else Fraction(y2 - y1) / (x2 - x1))
    x3 = slope * slope - x1 - x2
    return x3, slope * (x1 - x3) - y1


def rational_mul(k, point):
    if k < 0:
        return rational_mul(-k, (point[0], -point[1]))
    result = O
    while k:
        if k & 1:
            result = rational_add(result, point)
        point = rational_add(point, point)
        k >>= 1
    return result


def lift(point, p, shifts):
    if point is O:
        return {"status": "identity", "probes": 0}
    x0 = point[0] if point[0] <= p // 2 else point[0] - p
    for count, shift in enumerate(shifts, 1):
        x = x0 + shift * p
        f = x * x * x - x - 2
        if f < 0:
            continue
        y0 = isqrt(f)
        if y0 * y0 != f:
            continue
        for y in (y0, -y0):
            if y % p == point[1]:
                return {"status": "lifted", "probes": count,
                        "shift": shift, "rational_point": [x, y]}
    return {"status": "window_exhausted", "probes": len(shifts)}


def family():
    return [(a, b) for a in range(1, 4) for b in range(-3, 4)
            if b and gcd(a, abs(b)) == 1]


def run_field(item, shifts):
    p, q = item["field_prime"], item["subgroup_order"]
    P = (2 % p, 2 % p)
    order = point_order(P, p, item["curve_order"])
    assert order % q == 0
    m = order // q
    G = mul(m, P, p)
    assert mul(q, G, p) is O and G is not O
    Q = mul(17, G, p)
    rows = []
    for t in range(q):
        R = add(Q, mul(-t, G, p), p)
        attempt = lift(R, p, shifts)
        rows.append({"t": t, "reduced_point": list(R) if R else None, **attempt})
    path = HERE / "rows" / f"p{p}.jsonl.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as out:
            for row in rows:
                out.write((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode())
    lifted = [row for row in rows if row["status"] == "lifted"]
    tests = len(family()) * len(lifted) * (len(lifted) - 1)
    hits = []
    for first in lifted:
        for second in lifted:
            if first["t"] == second["t"]:
                continue
            A = tuple(first["rational_point"])
            B = tuple(second["rational_point"])
            for a, b in family():
                if rational_add(rational_mul(a, A), rational_mul(b, B)) is not O:
                    continue
                assert add(mul(a, tuple(first["reduced_point"]), p),
                           mul(b, tuple(second["reduced_point"]), p), p) is O
                useful = (a + b) % q != 0
                recovered = ((a * first["t"] + b * second["t"]) *
                             pow(a + b, -1, q)) % q if useful else None
                if useful:
                    assert recovered == 17
                hits.append({"t1": first["t"], "t2": second["t"],
                             "coefficients": [a, b], "useful": useful,
                             "recovered_scalar": recovered})
    return {"field_prime": p, "subgroup_order": q,
            "generator_reduction_order": order, "subgroup_multiplier_m": m,
            "queries": q, "identity_queries": 1,
            "point_lifts": len(lifted),
            "failed_point_lifts": q - 1 - len(lifted),
            "candidate_x_probes": sum(row["probes"] for row in rows),
            "ordered_admissible_lifted_pairs": len(lifted) * (len(lifted) - 1),
            "rational_group_tests": tests, "rational_relation_hits": hits,
            "rows_path": str(path.relative_to(HERE)), "rows_sha256": sha(path)}


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["schema"] == "xedni-public-coordinate-lift-protocol-v1"
    assert sha(INPUT) == protocol["input_selection_result_sha256"]
    selected = [x for x in json.loads(INPUT.read_text())["rows"] if x["selected"]]
    fields = [run_field(item, protocol["lift_rule"]["shift_order"]) for item in selected]
    result = {"schema": "xedni-public-coordinate-lift-result-v1",
              "status": "PASS", "protocol_sha256": sha(HERE / "protocol.json"),
              "source_sha256": sha(Path(__file__)), "input_sha256": sha(INPUT),
              "fields": fields,
              "totals": {key: sum(field[key] for field in fields) for key in (
                  "queries", "identity_queries", "point_lifts", "failed_point_lifts",
                  "candidate_x_probes", "ordered_admissible_lifted_pairs",
                  "rational_group_tests")},
              "total_rational_relation_hits": sum(len(f["rational_relation_hits"])
                                                  for f in fields)}
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
