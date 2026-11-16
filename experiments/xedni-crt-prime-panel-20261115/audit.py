"""Independent exact arithmetic audit of every cross-prime CRT panel row."""

import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR_AUDIT = HERE.parent / "xedni-crt-curve-choice-20261115" / "cost_audit.py"
spec = importlib.util.spec_from_file_location("xedni_crt_cost_audit", PRIOR_AUDIT)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def add(left, right, coefficients, prime=None):
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    a1, a2, a3, a4, _ = coefficients
    if prime is None:
        x1, y1, x2, y2 = map(Fraction, (x1, y1, x2, y2))
        a1, a2, a3, a4 = map(Fraction, (a1, a2, a3, a4))
    if x1 == x2 and ((y1 + y2 + a1 * x2 + a3) % prime == 0 if prime
                     else y1 + y2 + a1 * x2 + a3 == 0):
        return None
    if x1 == x2:
        numerator = 3 * x1 * x1 + 2 * a2 * x1 + a4 - a1 * y1
        denominator = 2 * y1 + a1 * x1 + a3
    else:
        numerator = y2 - y1
        denominator = x2 - x1
    slope = (numerator * pow(int(denominator) % prime, -1, prime)) % prime \
        if prime else numerator / denominator
    x3 = slope * slope + a1 * slope - a2 - x1 - x2
    y3 = -(slope + a1) * x3 - y1 + slope * x1 - a3
    return (int(x3) % prime, int(y3) % prime) if prime else (x3, y3)


def neg(point, coefficients, prime):
    if point is None:
        return None
    x, y = point
    return (x, (-y - coefficients[0] * x - coefficients[2]) % prime)


def mul(k, point, coefficients, prime):
    result = None
    while k:
        if k & 1:
            result = add(result, point, coefficients, prime)
        point = add(point, point, coefficients, prime)
        k //= 2
    return result


def field_points(p, coefficients):
    a1, a2, a3, a4, a6 = coefficients
    return [(x, y) for x in range(p) for y in range(p)
            if (y * y + a1 * x * y + a3 * y -
                (x ** 3 + a2 * x * x + a4 * x + a6)) % p == 0]


def largest_prime_factor(n):
    largest = 1
    factor = 2
    while factor * factor <= n:
        while n % factor == 0:
            largest = factor
            n //= factor
        factor += 1
    return max(largest, n)


def centered(value, p):
    return value if value <= p // 2 else value - p


def crt_free(p, residue7, residue11):
    return next(centered_multiple(p * k, 77 * p) for k in range(77)
                if (p * k) % 7 == residue7 and (p * k) % 11 == residue11)


def centered_multiple(value, modulus):
    return value if value <= modulus // 2 else value - modulus


def solve_rational(points, free):
    (x1, y1), (x2, y2) = points
    a1, a2, a3 = free
    v1 = y1 * y1 + a1 * x1 * y1 + a3 * y1 - x1 ** 3 - a2 * x1 * x1
    v2 = y2 * y2 + a1 * x2 * y2 + a3 * y2 - x2 ** 3 - a2 * x2 * x2
    a4 = Fraction(v1 - v2, x1 - x2)
    a6 = Fraction(v1) - a4 * x1
    return (*free, a4, a6)


def delta(coefficients):
    a1, a2, a3, a4, a6 = coefficients
    b2 = a1 * a1 + 4 * a2
    b4 = a1 * a3 + 2 * a4
    b6 = a3 * a3 + 4 * a6
    b8 = a1 * a1 * a6 + 4 * a2 * a6 - a1 * a3 * a4 + a2 * a3 * a3 - a4 * a4
    return -b2 * b2 * b8 - 8 * b4 ** 3 - 27 * b6 ** 2 + 9 * b2 * b4 * b6


def mod_rational(value, prime):
    value = Fraction(value)
    return (value.numerator * pow(value.denominator % prime, -1, prime)) % prime


def check_prime(record, protocol, orders, chars):
    p = record["field_prime"]
    base = protocol["base_curve_coefficients"]
    points = field_points(p, base)
    n = len(points) + 1
    r = largest_prime_factor(n)
    assert (n, r) == (record["curve_order"], record["subgroup_order"])
    if record["status"] == "subgroup_too_small":
        assert r < protocol["subgroup_policy"]["required_minimum_order"]
        return 0
    assert record["status"] == "PASS"
    h = n // r
    generator = next(mul(h, point, base, p) for point in points
                     if mul(h, point, base, p) is not None)
    w = 17 if r > 17 else 1
    public = mul(w, generator, base, p)
    assert list(generator) == record["generator"]
    assert list(public) == record["public_target"] and w == record["fixture_scalar"]
    assert mul(r, generator, base, p) is None
    sampled = [add(public, neg(mul(t, generator, base, p), base, p), base, p)
               for t in range(r)]
    counts = Counter()
    first = None
    raw_hash = hashlib.sha256()
    index = 0
    for shard in record["row_shards"]:
        raw = gzip.open(HERE / "rows" / shard, "rb").read()
        raw_hash.update(raw)
        for line in raw.splitlines():
            saved = json.loads(line)
            t1, t2 = divmod(index, r)
            index += 1
            assert saved["t"] == [t1, t2]
            P1, P2 = sampled[t1], sampled[t2]
            counts["target_queries"] += 1
            status = None
            accepted = reduced = rational = False
            attempts7 = attempts11 = 0
            recovered = None
            if P1 is None or P2 is None:
                status = "identity"
            elif P1 == P2:
                status = "duplicate"
            else:
                counts["admissible_pairs"] += 1
                reduced = add(P1, mul(2, P2, base, p), base, p) is None
                lifted = [(centered(x, p), centered(y, p)) for x, y in (P1, P2)]
                dx = lifted[0][0] - lifted[1][0]
                if dx == 0:
                    status = "same_x_base"
                elif dx % 7 == 0:
                    status = "same_x_7"
                elif dx % 11 == 0:
                    status = "same_x_11"
                else:
                    c7, attempts7 = prior.find_candidate(lifted, 7, 4, orders[7], chars[7])
                    counts["attempts_7"] += attempts7
                    if c7 is None:
                        status = "no_order_4_at_7"
                    else:
                        c11, attempts11 = prior.find_candidate(lifted, 11, 6,
                                                                orders[11], chars[11])
                        counts["attempts_11"] += attempts11
                        if c11 is None:
                            status = "no_order_6_at_11"
                        else:
                            free = tuple(crt_free(p, c7[i], c11[i]) for i in range(3))
                            coefficients = solve_rational(lifted, free)
                            if delta(coefficients) == 0:
                                status = "singular_rational_curve"
                            else:
                                for prime, expected in ((p, [0, 0, 0, p - 1, p - 2]),
                                                        (7, c7), (11, c11)):
                                    assert [mod_rational(x, prime) for x in coefficients] == list(expected)
                                    assert mod_rational(delta(coefficients), prime) != 0
                                status = "accepted"
                                accepted = True
                                counts["accepted_pairs"] += 1
                                if reduced:
                                    counts["accepted_reduced_relations"] += 1
                                    rational = add(lifted[0],
                                                   mul(2, lifted[1], coefficients, None),
                                                   coefficients, None) is None
                                    if rational:
                                        counts["accepted_rational_relations"] += 1
                                        recovered = ((t1 + 2 * t2) * pow(3, -1, r)) % r
                                        assert recovered == w
                                        if first is None:
                                            first = {"t": [t1, t2],
                                                     "query_index_one_based": index}
            counts[f"status_{status}"] += 1
            if first is not None and "counters" not in first:
                first["counters"] = dict(counts)
            expected = {"t": [t1, t2], "status": status, "accepted": accepted,
                        "reduced_relation": reduced, "rational_relation": rational,
                        "attempts_7": attempts7, "attempts_11": attempts11}
            if recovered is not None:
                expected["recovered_scalar"] = recovered
            assert saved == expected, (p, t1, t2, saved, expected)
    assert index == r * r and raw_hash.hexdigest() == record["rows_sha256"]
    assert dict(counts) == record["counts"], (p, dict(counts), record["counts"])
    assert first == record["first_rational_relation"]
    return index


def main():
    protocol_path = HERE / "protocol.json"
    protocol = json.loads(protocol_path.read_text())
    result = json.loads((HERE / "result.json").read_text())
    assert result["status"] == "PASS" and result["protocol_sha256"] == sha(protocol_path.read_bytes())
    assert result["source_sha256"] == sha((HERE / "run.py").read_bytes())
    assert result["parent_source_sha256"] == protocol["parent_search_source_sha256"]
    assert sha(PRIOR_AUDIT.read_bytes()) == "565365e0e9093dcc512cc551bb19760b4f6aa54538093c557dc1acd1cdf645f7"
    assert result["sage_runtime_sha256"] == sha((HERE / "sage-runtime-info.json").read_bytes())
    assert [field["field_prime"] for field in result["fields"]] == protocol["base_field_primes"]
    assert set((HERE / "rows").glob("*.jsonl.gz")) == {
        HERE / "rows" / shard for field in result["fields"] for shard in field.get("row_shards", [])}
    orders = {prime: prior.candidates(prime) for prime in (7, 11)}
    chars = {}
    for prime in orders:
        squares = {x * x % prime for x in range(1, prime)}
        chars[prime] = [0 if x == 0 else 1 if x in squares else -1
                        for x in range(prime)]
    checked = [check_prime(record, protocol, orders, chars) for record in result["fields"]]
    reference = json.loads((HERE.parent / "xedni-crt-curve-choice-20261115" / "result-target.json").read_text())
    reference_cost = json.loads((HERE.parent / "xedni-crt-curve-choice-20261115" / "cost-result.json").read_text())
    panel47 = result["fields"][0]["counts"]
    assert panel47["target_queries"] == reference["target_queries"]
    assert panel47["accepted_pairs"] == reference["crt_accepted_pairs"]
    assert panel47["accepted_rational_relations"] == reference["accepted_rational_relations"]
    assert panel47["attempts_7"] == reference_cost["complete_scan"]["attempts_7"]
    assert panel47["attempts_11"] == reference_cost["complete_scan"]["attempts_11_strict"]
    assert result["fields"][0]["first_rational_relation"]["t"] == \
        reference_cost["first_accepted_rational_relation"]["t"]
    print(json.dumps({"status": "PASS", "schema": "xedni-crt-prime-panel-audit-v1",
                      "source_sha256": sha(Path(__file__).read_bytes()),
                      "prior_audit_source_sha256": sha(PRIOR_AUDIT.read_bytes()),
                      "total_queries_audited": sum(checked),
                      "field_statuses": {str(x["field_prime"]): x["status"] for x in result["fields"]}},
                     sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
