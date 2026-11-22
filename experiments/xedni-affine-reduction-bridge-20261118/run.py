#!/usr/bin/env python3
"""Independent exact replay of rational lift addition and public reduction."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "xedni-known-relation-lifts-20261118" / "run-result.json"
PROTOCOL = HERE / "protocol.json"


def canonical(obj):
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode()


def unit_den(z, p):
    return z.denominator % p != 0


def reduce_number(z, p):
    if not unit_den(z, p):
        raise ValueError("nonunit_coordinate_denominator")
    return (z.numerator * pow(z.denominator, -1, p)) % p


def reduce_point(P, p):
    return None if P is None else [reduce_number(z, p) for z in P]


def on_curve(P, A, B):
    return P is None or P[1] * P[1] == P[0] ** 3 + A * P[0] + B


def negate(P):
    return None if P is None else (P[0], -P[1])


def add_rat(P, Q, A):
    if P is None:
        return Q, "identity", None
    if Q is None:
        return P, "identity", None
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2 and y1 == -y2:
        return None, "vertical", None
    if x1 == x2:
        assert y1 == y2
        numerator, denominator, branch = 3 * x1 * x1 + A, 2 * y1, "tangent"
    else:
        numerator, denominator, branch = y2 - y1, x2 - x1, "chord"
    assert denominator != 0
    slope = numerator / denominator
    x3 = slope * slope - x1 - x2
    y3 = slope * (x1 - x3) - y1
    return (x3, y3), branch, (numerator, denominator, slope)


def add_mod(P, Q, A, p):
    if P is None:
        return Q
    if Q is None:
        return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2 and (y1 + y2) % p == 0:
        return None
    if x1 == x2:
        assert y1 == y2
        numerator, denominator = (3 * x1 * x1 + A) % p, (2 * y1) % p
    else:
        numerator, denominator = (y2 - y1) % p, (x2 - x1) % p
    assert denominator != 0
    slope = numerator * pow(denominator, -1, p) % p
    x3 = (slope * slope - x1 - x2) % p
    y3 = (slope * (x1 - x3) - y1) % p
    return [x3, y3]


def parse_point(raw):
    return None if raw is None else tuple(Fraction(int(z["num"]), int(z["den"])) for z in raw)


def main():
    source_bytes = SOURCE.read_bytes()
    protocol_bytes = PROTOCOL.read_bytes()
    protocol = json.loads(protocol_bytes)
    assert hashlib.sha256(source_bytes).hexdigest() == protocol["source_sha256"]
    source = json.loads(source_bytes)
    assert source["schema"] == "xedni-known-relation-lifts-result-v1"
    rows = []
    for source_row in source["rows"]:
        if source_row["status"] != "exact_relation":
            continue
        hit = source_row["hit"]
        p, q, a, b = (hit[k] for k in ("p", "q", "a", "b"))
        A, B = source_row["model"]["A"], source_row["model"]["B"]
        T = tuple(Fraction(z) for z in source_row["model"]["T"])
        assert on_curve(T, A, B)
        max_n = max(abs(b), abs(a))
        P, Pmod = T, reduce_point(T, p)
        assert Pmod == source_row["R"]
        steps = []
        multiples = {1: T}
        for n in range(1, max_n):
            previous, previous_mod = P, Pmod
            P, branch, slope_data = add_rat(previous, T, A)
            assert on_curve(P, A, B)
            input_integral = all(unit_den(z, p) for point in (previous, T) for z in point)
            denominator_unit = slope_data is None or (unit_den(slope_data[1], p) and reduce_number(slope_data[1], p) != 0)
            slope_integral = slope_data is None or unit_den(slope_data[2], p)
            output_integral = P is None or all(unit_den(z, p) for z in P)
            regular = input_integral and denominator_unit and slope_integral and output_integral
            reduced = reduce_point(P, p) if output_integral else None
            expected = add_mod(previous_mod, reduce_point(T, p), A, p) if input_integral else None
            matches = reduced == expected if regular else None
            assert regular and matches is True
            steps.append({"from_multiple": n, "to_multiple": n + 1, "branch": branch,
                          "input_integral": input_integral, "slope_denominator_unit": denominator_unit,
                          "slope_integral": slope_integral, "output_integral": output_integral,
                          "regular": regular, "reduction_matches": matches})
            multiples[n + 1] = P
            Pmod = reduced
        P1 = multiples[abs(b)] if b > 0 else negate(multiples[abs(b)])
        P2 = negate(multiples[abs(a)]) if a > 0 else multiples[abs(a)]
        assert P1 == parse_point(source_row["P1"])
        assert P2 == parse_point(source_row["P2"])
        assert reduce_point(P1, p) == hit["U"]
        assert reduce_point(P2, p) == hit["V"]
        rows.append({"hit_index": source_row["hit_index"], "p": p, "q": q, "a": a, "b": b,
                     "max_multiple": max_n, "steps": steps,
                     "regular_steps": sum(s["regular"] for s in steps),
                     "exceptional_steps": sum(not s["regular"] for s in steps)})
    assert len(rows) == 13
    result = {"schema": "xedni-affine-reduction-bridge-result-v1", "status": "complete",
              "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
              "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(), "rows": rows}
    (HERE / "result.json").write_bytes(canonical(result))
    print(json.dumps({"hits": len(rows), "steps": sum(len(r["steps"]) for r in rows),
                      "regular_steps": sum(r["regular_steps"] for r in rows),
                      "exceptional_steps": sum(r["exceptional_steps"] for r in rows)}, sort_keys=True))


if __name__ == "__main__":
    main()
