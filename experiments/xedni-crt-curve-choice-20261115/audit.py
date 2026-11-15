"""Independent exact audit of the restricted and full CRT curve censuses."""

import hashlib
import gzip
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent


def data_bytes(name):
    path = HERE / name
    if path.exists():
        return path.read_bytes()
    assert name.endswith(".jsonl")
    return gzip.decompress((HERE / (name + ".gz")).read_bytes())


def sha(name):
    return hashlib.sha256(data_bytes(name)).hexdigest()


def centered(n, p):
    return n if n <= p // 2 else n - p


def add_short(P, Q, a, p):
    if P is None:
        return Q
    if Q is None:
        return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2 and (y1 + y2) % p == 0:
        return None
    numerator = 3 * x1 * x1 + a if P == Q else y2 - y1
    denominator = 2 * y1 if P == Q else x2 - x1
    slope = numerator * pow(denominator % p, -1, p) % p
    x3 = (slope * slope - x1 - x2) % p
    y3 = (slope * (x1 - x3) - y1) % p
    return x3, y3


def mul_short(n, P, a, p):
    result = None
    while n:
        if n & 1:
            result = add_short(result, P, a, p)
        P = add_short(P, P, a, p)
        n //= 2
    return result


def neg_short(P, p):
    return None if P is None else (P[0], -P[1] % p)


def curve_order(coeffs, p):
    a1, a2, a3, a4, a6 = coeffs
    return 1 + sum((y * y + a1 * x * y + a3 * y - x ** 3 - a2 * x * x - a4 * x - a6) % p == 0
                   for x in range(p) for y in range(p))


def discriminant(a1, a2, a3, a4, a6):
    b2 = a1 * a1 + 4 * a2
    b4 = a1 * a3 + 2 * a4
    b6 = a3 * a3 + 4 * a6
    b8 = a1 * a1 * a6 + 4 * a2 * a6 - a1 * a3 * a4 + a2 * a3 * a3 - a4 * a4
    return -b2 * b2 * b8 - 8 * b4 ** 3 - 27 * b6 * b6 + 9 * b2 * b4 * b6


def rational_relation(P1, P2, coeffs):
    a1, a2, a3, a4, _ = coeffs
    x, y = map(Fraction, P2)
    denominator = 2 * y + a1 * x + a3
    if denominator == 0:
        return False
    slope = (3 * x * x + 2 * a2 * x + a4 - a1 * y) / denominator
    intercept = y - slope * x
    x_double = slope * slope + a1 * slope - a2 - 2 * x
    y_double = -(slope + a1) * x_double - intercept - a3
    minus_double = (x_double, -y_double - a1 * x_double - a3)
    return tuple(map(Fraction, P1)) == minus_double


def check_receipt(suffix, source):
    protocol = f"protocol{suffix}.json"
    result = json.loads((HERE / f"result{suffix}.json").read_text())
    rows_name = f"rows{suffix}.jsonl"
    assert result["status"] == "PASS"
    assert result["protocol_sha256"] == sha(protocol)
    assert result["source_sha256"] == sha(source)
    assert result["sage_runtime_sha256"] == sha(f"sage-runtime-info{suffix}.json")
    assert result["rows_sha256"] == sha(rows_name)
    assert (HERE / f"run{suffix}.stderr").stat().st_size == 0
    rows = [json.loads(line) for line in data_bytes(rows_name).decode().splitlines()]
    assert len(rows) == result["total_ordered_pairs"] == 1722
    return rows, result


def check_target(catalog):
    protocol = json.loads((HERE / "protocol-target.json").read_text())
    result = json.loads((HERE / "result-target.json").read_text())
    compressed = (HERE / "target-rows.jsonl.gz").read_bytes()
    raw = gzip.decompress(compressed)
    assert result["status"] == "PASS"
    assert result["protocol_sha256"] == sha("protocol-target.json")
    assert result["source_sha256"] == sha("target_replay.py")
    assert result["parent_source_sha256"] == protocol["parent_source_sha256"] == sha("run_v2.py")
    assert result["parent_rows_sha256"] == protocol["parent_census_rows_sha256"] == sha("rows-v2.jsonl")
    assert result["runtime_sha256"] == sha("sage-runtime-info-target.json")
    assert result["target_rows_sha256"] == hashlib.sha256(raw).hexdigest()
    assert result["target_rows_gzip_sha256"] == hashlib.sha256(compressed).hexdigest()
    assert (HERE / "target.stderr").stat().st_size == 0
    target_rows = [json.loads(line) for line in raw.decode().splitlines()]
    assert len(target_rows) == result["target_queries"] == 43 * 43
    lookup = {tuple(tuple(point) for point in row["reduced_points"]): row for row in catalog}
    assert len(lookup) == 1722
    G, Q = tuple(result["generator"]), tuple(result["public_target"])
    assert G == (2, 2) and Q == (26, 8)
    assert mul_short(43, G, -1, 47) is None
    assert mul_short(17, G, -1, 47) == Q
    counts = Counter()
    accepted = reduced = rational = 0
    hits = []
    for index, row in enumerate(target_rows):
        t1, t2 = divmod(index, 43)
        assert row["t"] == [t1, t2]
        P1 = add_short(Q, neg_short(mul_short(t1, G, -1, 47), 47), -1, 47)
        P2 = add_short(Q, neg_short(mul_short(t2, G, -1, 47), 47), -1, 47)
        if P1 is None or P2 is None:
            assert row["status"] == "identity"
        elif P1 == P2:
            assert row["status"] == "duplicate"
        else:
            prior = lookup[(P1, P2)]
            assert row["reduced_points"] == [list(P1), list(P2)]
            assert row["status"] == prior["status"]
            assert row["accepted"] == prior["accepted"]
            assert row["reduced_relation"] == prior["reduced_relation"]
            assert row["rational_relation"] == prior["rational_relation"]
            accepted += int(row["accepted"])
            reduced += int(row["accepted"] and row["reduced_relation"])
            rational += int(row["rational_relation"])
            if row["rational_relation"]:
                scalar = (t1 + 2 * t2) * pow(3, -1, 43) % 43
                assert scalar == row["recovered_scalar"] == 17
                assert mul_short(scalar, G, -1, 47) == Q
                hits.append({"t": row["t"], "scalar": scalar})
        counts[row["status"]] += 1
    assert counts == result["status_counts"]
    assert (accepted, reduced, rational) == (
        result["crt_accepted_pairs"], result["accepted_reduced_relations"],
        result["accepted_rational_relations"])
    assert [item["scalar"] for item in hits] == result["recovered_scalars"]
    return {"target_queries": len(target_rows), "target_hits": hits,
            "target_status": "PASS"}


def main():
    old, old_result = check_receipt("", "run.py")
    rows, result = check_receipt("-v2", "run_v2.py")
    assert old_result["accepted_pairs"] == 0
    assert old_result["status_counts"]["no_order_6_or_7_at_11"] == 88
    assert len(old) == len(rows)
    assert all(a["reduced_points"] == b["reduced_points"] for a, b in zip(old, rows))
    seen = set()
    statuses = Counter()
    reduced_hits = accepted = accepted_reduced = accepted_rational = 0
    strict = weak = 0
    curves = set()
    rational_examples = []
    for row in rows:
        P1, P2 = (tuple(point) for point in row["reduced_points"])
        assert P1 != P2
        seen.add((P1, P2))
        for x, y in (P1, P2):
            assert (y * y - x ** 3 + x + 2) % 47 == 0
        lifted = [tuple(point) for point in row["lifted_points"]]
        assert lifted == [(centered(x, 47), centered(y, 47)) for x, y in (P1, P2)]
        reduced = add_short(P1, add_short(P2, P2, -1, 47), -1, 47) is None
        assert reduced == row["reduced_relation"]
        reduced_hits += int(reduced)
        dx = lifted[0][0] - lifted[1][0]
        expected_status = ("same_x_47" if dx == 0 else
                           "same_x_7" if dx % 7 == 0 else
                           "same_x_11" if dx % 11 == 0 else "accepted")
        assert row["status"] == expected_status
        statuses[expected_status] += 1
        if not row["accepted"]:
            assert not row["rational_relation"]
            continue
        accepted += 1
        accepted_reduced += int(reduced)
        assert row["arm"] in ("strict", "weak")
        strict += int(row["arm"] == "strict")
        weak += int(row["arm"] == "weak")
        coeffs = [Fraction(row[key]) for key in ("a1", "a2", "a3", "a4", "a6")]
        a1, a2, a3, a4, a6 = coeffs
        curves.add(tuple(coeffs))
        assert discriminant(*coeffs) != 0
        for x, y in lifted:
            assert y * y + a1 * x * y + a3 * y == x ** 3 + a2 * x * x + a4 * x + a6
        for prime, wanted, saved in ((47, 43, [0, 0, 0, 46, 45]),
                                     (7, 4, row["chosen_residues_7"]),
                                     (11, 6 if row["arm"] == "strict" else 7, row["chosen_residues_11"])):
            assert all(c.denominator % prime for c in coeffs)
            residues = [c.numerator * pow(c.denominator, -1, prime) % prime for c in coeffs]
            assert residues == saved
            assert discriminant(*residues) % prime != 0
            assert curve_order(residues, prime) == wanted
        relation = rational_relation(lifted[0], lifted[1], coeffs) if reduced else False
        assert relation == row["rational_relation"]
        accepted_rational += int(relation)
        if relation:
            rational_examples.append({"reduced_points": row["reduced_points"],
                                      "coefficients": [str(c) for c in coeffs]})
    assert len(seen) == 1722
    assert statuses == result["status_counts"]
    assert (reduced_hits, accepted, accepted_reduced, accepted_rational, strict, weak) == (
        result["full_reduced_relation_pairs"], result["accepted_pairs"],
        result["accepted_reduced_relation_pairs"], result["accepted_rational_relation_pairs"],
        result["strict_accepted_pairs"], result["weak_accepted_pairs"])
    assert len(rational_examples) == 2
    assert (HERE / "run-failed.stderr").stat().st_size > 0
    assert (HERE / "rows-failed.jsonl").stat().st_size == 0
    target_audit = check_target(rows)
    print(json.dumps({"status": "PASS", "audited_pairs": len(rows),
                      "accepted_pairs": accepted, "distinct_accepted_curves": len(curves),
                      "accepted_reduced_relation_pairs": accepted_reduced,
                      "accepted_rational_relation_pairs": accepted_rational,
                      "rational_relation_examples": rational_examples,
                      **target_audit,
                      "initial_producer_failure_preserved": True}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
