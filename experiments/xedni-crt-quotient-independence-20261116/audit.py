"""Independent pure-Python replay of every finite-field quotient calculation."""
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "xedni-optimized-family-lift-replay-20261115"
protocol = json.loads((HERE / "protocol.json").read_text())
summary = json.loads((HERE / "result.json").read_text())
parent = json.loads((PARENT / "result.json").read_text())
assert summary["status"] == "complete" and summary["processed_rows"] == 9688
assert hashlib.sha256((PARENT / "SEAL.sha256").read_bytes()).hexdigest() == protocol["parent_seal_sha256"]


def mod(q, p):
    q = Fraction(q)
    return q.numerator * pow(q.denominator, -1, p) % p


def neg(P, a1, a3, p):
    return None if P is None else (P[0], (-P[1]-a1*P[0]-a3) % p)


def add(P, Q, a, p):
    if P is None:
        return Q
    if Q is None:
        return P
    a1, a2, a3, a4, _ = a
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2 and Q == neg(P, a1, a3, p):
        return None
    if P == Q:
        den = (2*y1+a1*x1+a3) % p
        assert den != 0
        slope = (3*x1*x1+2*a2*x1+a4-a1*y1) * pow(den, -1, p) % p
    else:
        assert x1 != x2
        slope = (y2-y1) * pow((x2-x1) % p, -1, p) % p
    intercept = (y1-slope*x1) % p
    x3 = (slope*slope+a1*slope-a2-x1-x2) % p
    y3 = (-(slope+a1)*x3-intercept-a3) % p
    return x3, y3


def curve_points(a, p):
    a1, a2, a3, a4, a6 = a
    square_roots = {}
    for y in range(p):
        square_roots.setdefault(y*y % p, []).append(y)
    inv2 = pow(2, -1, p)
    points = []
    for x in range(p):
        linear = (a1*x+a3) % p
        rhs = (x*x*x+a2*x*x+a4*x+a6) % p
        for root in square_roots.get((linear*linear+4*rhs) % p, []):
            y = (-linear+root)*inv2 % p
            assert (y*y+a1*x*y+a3*y-rhs) % p == 0
            points.append((x, y))
    return points


def discriminant(a, p):
    a1, a2, a3, a4, a6 = a
    b2 = a1*a1+4*a2
    b4 = 2*a4+a1*a3
    b6 = a3*a3+4*a6
    b8 = a1*a1*a6+4*a2*a6-a1*a3*a4+a2*a3*a3-a4*a4
    return (-b2*b2*b8-8*b4*b4*b4-27*b6*b6+9*b2*b4*b6) % p


cache = {}
counts = Counter()
files = 0
total_models = 0
for arm in parent["arms"]:
    for spec in arm["fields"]:
        cache.clear()
        source = PARENT / spec["tests_path"]
        output = HERE / "rows" / spec["tests_path"]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == spec["tests_sha256"]
        expected_output = next(r for r in summary["by_arm_field"] if r["source_path"] == spec["tests_path"])
        assert hashlib.sha256(output.read_bytes()).hexdigest() == expected_output["output_sha256"]
        local = Counter()
        with source.open() as original, output.open() as measured:
            for index, (source_line, output_line) in enumerate(zip(original, measured)):
                row = json.loads(source_line)
                record = json.loads(output_line)
                assert record["source_ordinal_zero_based"] == index
                assert record["source_path"] == spec["tests_path"]
                assert record["query_index_one_based"] == row["query_index_one_based"]
                assert record["vector"] == row["vector"]
                assert record["rational_relation"] == row["rational_relation"]
                coefficients = [Fraction(c) for c in row["coefficients"]]
                odd_prime = quotient_prime = None
                assert len(record["prime_checks"]) <= len(protocol["ordered_primes"])
                for prime, check in zip(protocol["ordered_primes"], record["prime_checks"]):
                    assert check["prime"] == prime
                    if any(c.denominator % prime == 0 for c in coefficients):
                        assert check["status"] == "nonintegral"
                        continue
                    a = tuple(mod(c, prime) for c in coefficients)
                    if discriminant(a, prime) == 0:
                        assert check["status"] == "bad_reduction"
                        continue
                    assert check["status"] == "complete"
                    key = (prime, a)
                    if key not in cache:
                        points = curve_points(a, prime)
                        doubled = {add(T, T, a, prime) for T in points + [None]} if (len(points)+1) % 4 == 0 else None
                        cache[key] = (len(points)+1, doubled)
                    group_order, doubled = cache[key]
                    assert check["curve_order"] == group_order
                    assert check["odd_order"] == bool(group_order % 2)
                    P, Q = [tuple(v % prime for v in pair) for pair in row["points"]]
                    a1, a2, a3, a4, a6 = a
                    for x, y in (P, Q):
                        assert (y*y+a1*x*y+a3*y-x*x*x-a2*x*x-a4*x-a6) % prime == 0
                    if odd_prime is None and group_order % 2:
                        odd_prime = prime
                    tests = None
                    if quotient_prime is None and group_order % 4 == 0:
                        assert doubled is not None
                        tests = [P not in doubled, Q not in doubled, add(P, Q, a, prime) not in doubled]
                        if all(tests):
                            quotient_prime = prime
                    assert check["quotient_nonzero_tests"] == tests
                if odd_prime is not None and quotient_prime is not None:
                    assert record["prime_checks"][-1]["prime"] == max(odd_prime, quotient_prime)
                else:
                    assert len(record["prime_checks"]) == len(protocol["ordered_primes"])
                assert record["odd_order_prime"] == odd_prime
                assert record["quotient_prime"] == quotient_prime
                status = ("certified_independent" if odd_prime is not None and quotient_prime is not None else
                          "quotient_only" if quotient_prime is not None else
                          "torsion_only" if odd_prime is not None else "neither")
                assert record["status"] == status
                counts[status] += 1
                local[status] += 1
                local["rows"] += 1
            assert next(original, None) is None and next(measured, None) is None
        assert local == Counter(expected_output["counts"])
        total_models += len(cache)
        files += 1
        print(spec["tests_path"], local["rows"], flush=True)
assert files == 16 and sum(counts.values()) == 9688
for status in ("certified_independent", "quotient_only", "torsion_only", "neither"):
    assert counts[status] == summary[status]
receipt = {"status": "PASS", "files": files, "rows": 9688, "finite_curve_models_recomputed": total_models,
           "counts": dict(counts), "method": "independent Python general Weierstrass group law and point enumeration"}
(HERE / "audit.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(json.dumps(receipt, sort_keys=True))
