"""Independent Python arithmetic replay of the extended finite quotients."""
import hashlib
import json
from collections import Counter
from fractions import Fraction
from math import gcd, isqrt, lcm
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "xedni-crt-quotient-independence-20261116"
ARCHIVE = HERE.parent / "xedni-optimized-family-lift-replay-20261115"
protocol = json.loads((HERE / "protocol.json").read_text())
summary = json.loads((HERE / "result.json").read_text())
prior_result = json.loads((PARENT / "result.json").read_text())
archive_result = json.loads((ARCHIVE / "result.json").read_text())
assert summary["status"] == "complete"
assert hashlib.sha256((PARENT / "SEAL.sha256").read_bytes()).hexdigest() == protocol["parent_seal_sha256"]
assert hashlib.sha256((HERE / "rows.jsonl").read_bytes()).hexdigest() == summary["rows_sha256"]


def prime_list(lo, hi):
    return [n for n in range(lo, hi) if n > 1 and all(n % d for d in range(2, isqrt(n)+1))]


PRIMES = prime_list(101, 500)
assert len(PRIMES) == summary["prime_count"]
assert PRIMES[0] == summary["first_prime"] and PRIMES[-1] == summary["last_prime"]


def field(q, p):
    q = Fraction(q)
    return q.numerator * pow(q.denominator, -1, p) % p


def inverse_point(P, a, p):
    return None if P is None else (P[0], (-P[1]-a[0]*P[0]-a[2]) % p)


def sum_points(P, Q, a, p):
    if P is None:
        return Q
    if Q is None:
        return P
    a1, a2, a3, a4, _ = a
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2 and Q == inverse_point(P, a, p):
        return None
    if P == Q:
        den = (2*y1+a1*x1+a3) % p
        slope = (3*x1*x1+2*a2*x1+a4-a1*y1) * pow(den, -1, p) % p
    else:
        slope = (y2-y1) * pow((x2-x1) % p, -1, p) % p
    intercept = (y1-slope*x1) % p
    x3 = (slope*slope+a1*slope-a2-x1-x2) % p
    return x3, (-(slope+a1)*x3-intercept-a3) % p


def finite_points(a, p):
    a1, a2, a3, a4, a6 = a
    squares = {}
    for y in range(p):
        squares.setdefault(y*y % p, []).append(y)
    inv2 = pow(2, -1, p)
    out = []
    for x in range(p):
        linear = (a1*x+a3) % p
        rhs = (x*x*x+a2*x*x+a4*x+a6) % p
        for root in squares.get((linear*linear+4*rhs) % p, []):
            y = (-linear+root)*inv2 % p
            assert (y*y+a1*x*y+a3*y-rhs) % p == 0
            out.append((x, y))
    return out


def disc(a, p):
    a1, a2, a3, a4, a6 = a
    b2 = a1*a1+4*a2
    b4 = 2*a4+a1*a3
    b6 = a3*a3+4*a6
    b8 = a1*a1*a6+4*a2*a6-a1*a3*a4+a2*a3*a3-a4*a4
    return (-b2*b2*b8-8*b4*b4*b4-27*b6*b6+9*b2*b4*b6) % p


def divisors(n):
    n = abs(n)
    if n == 0:
        return [0]
    small = [d for d in range(1, isqrt(n)+1) if n % d == 0]
    return sorted(set(small + [n//d for d in small]))


def rational_2_roots(coefficients):
    a1, a2, a3, a4, a6 = coefficients
    b2 = a1*a1+4*a2
    b4 = 2*a4+a1*a3
    b6 = a3*a3+4*a6
    polynomial = [b6, 2*b4, b2, Fraction(4)]
    scale = lcm(*(c.denominator for c in polynomial))
    ints = [int(c*scale) for c in polynomial]
    roots = set()
    for u in divisors(ints[0]):
        for v in divisors(ints[3]):
            if gcd(u, v) != 1:
                continue
            for sign in (-1, 1):
                x = Fraction(sign*u, v)
                if sum(c*x**i for i, c in enumerate(ints)) == 0:
                    roots.add(x)
    return sorted(roots)


counts = Counter()
models = 0
new_rows = iter((HERE / "rows.jsonl").open())
for spec in prior_result["by_arm_field"]:
    path = spec["source_path"]
    original = ARCHIVE / path
    prior = PARENT / spec["output_path"]
    archive_spec = next(f for arm in archive_result["arms"] for f in arm["fields"] if f["tests_path"] == path)
    assert hashlib.sha256(original.read_bytes()).hexdigest() == archive_spec["tests_sha256"]
    assert hashlib.sha256(prior.read_bytes()).hexdigest() == spec["output_sha256"]
    local = Counter()
    cache = {}
    with original.open() as raw_stream, prior.open() as old_stream:
        for ordinal, (raw_line, old_line) in enumerate(zip(raw_stream, old_stream)):
            old = json.loads(old_line)
            if old["status"] == "certified_independent":
                continue
            raw = json.loads(raw_line)
            rec = json.loads(next(new_rows))
            assert rec["source_path"] == path and rec["source_ordinal_zero_based"] == ordinal
            assert rec["query_index_one_based"] == raw["query_index_one_based"]
            assert rec["vector"] == raw["vector"] and rec["parent_status"] == old["status"]
            coefficients = [Fraction(c) for c in raw["coefficients"]]
            quotient_prime = old["quotient_prime"]
            torsion_certificate = old["odd_order_prime"]
            if old["status"] == "quotient_only":
                roots = rational_2_roots(coefficients)
                assert rec["rational_2_torsion_x_roots"] == [str(root) for root in roots]
                assert rec["extended_prime_checks"] == []
                if not roots:
                    torsion_certificate = "rational_2_division_polynomial_has_no_root"
                    counts["new_torsion_certificates"] += 1
            else:
                assert old["status"] == "torsion_only" and quotient_prime is None
                assert rec["rational_2_torsion_x_roots"] is None
                checks = rec["extended_prime_checks"]
                assert len(checks) <= len(PRIMES)
                for prime, check in zip(PRIMES, checks):
                    assert check["prime"] == prime
                    if any(c.denominator % prime == 0 for c in coefficients):
                        assert check["status"] == "nonintegral"
                        continue
                    a = tuple(field(c, prime) for c in coefficients)
                    if disc(a, prime) == 0:
                        assert check["status"] == "bad_reduction"
                        continue
                    assert check["status"] == "complete"
                    key = (prime, a)
                    if key not in cache:
                        points = finite_points(a, prime)
                        doubles = {sum_points(T, T, a, prime) for T in points + [None]} if (len(points)+1) % 4 == 0 else None
                        cache[key] = (len(points)+1, doubles, set(points))
                    order, doubled, point_set = cache[key]
                    assert check["curve_order"] == order
                    tests = None
                    if order % 4 == 0:
                        P, Q = [tuple(v % prime for v in pair) for pair in raw["points"]]
                        assert P in point_set and Q in point_set
                        tests = [P not in doubled, Q not in doubled, sum_points(P, Q, a, prime) not in doubled]
                        if all(tests):
                            quotient_prime = prime
                            counts["new_quotient_certificates"] += 1
                    assert check["quotient_nonzero_tests"] == tests
                if quotient_prime is None:
                    assert len(checks) == len(PRIMES)
                else:
                    assert checks[-1]["prime"] == quotient_prime
            status = "certified_independent" if quotient_prime is not None and torsion_certificate is not None else old["status"]
            assert rec["quotient_prime"] == quotient_prime
            assert rec["torsion_certificate"] == torsion_certificate
            assert rec["status"] == status
            counts[status] += 1
            local[status] += 1
            local["rows"] += 1
    assert local == Counter(next(x for x in summary["by_arm_field"] if x["source_path"] == path)["counts"])
    models += len(cache)
    print(path, local["rows"], flush=True)
assert next(new_rows, None) is None
assert sum(counts[k] for k in ("certified_independent", "torsion_only", "quotient_only")) == 1801
assert counts["new_quotient_certificates"] == summary["new_quotient_certificates"]
assert counts["new_torsion_certificates"] == summary["new_torsion_certificates"]
assert counts["certified_independent"] + prior_result["certified_independent"] == summary["cumulative_certified"]
receipt = {"status": "PASS", "unresolved_parent_rows": 1801,
           "new_quotient_certificates": counts["new_quotient_certificates"],
           "new_torsion_certificates": counts["new_torsion_certificates"],
           "cumulative_certified": summary["cumulative_certified"],
           "still_torsion_only": counts["torsion_only"], "finite_model_evaluations": models,
           "method": "independent Python general Weierstrass arithmetic and rational-root theorem"}
(HERE / "audit.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(json.dumps(receipt, sort_keys=True))
