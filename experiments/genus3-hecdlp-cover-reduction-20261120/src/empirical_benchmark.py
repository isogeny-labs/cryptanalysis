#!/usr/bin/env python3
"""Toy empirical benchmark for rho and plane-quartic relation collection.

This measures two real algorithmic primitives at small sizes.  It is not an
end-to-end NIST DLP benchmark: the quartic side stops before sparse linear
algebra and individual-log descent, while the rho side uses safe-prime
multiplicative subgroups as a concrete generic group.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import random
import statistics
import sys
import time
import warnings
from pathlib import Path

import sympy
from sympy.utilities.exceptions import SymPyDeprecationWarning


def fit_log_slope(rows, x_key, y_key):
    points = [(math.log(row[x_key]), math.log(row[y_key])) for row in rows if row[y_key] > 0]
    mean_x = statistics.fmean(x for x, _ in points)
    mean_y = statistics.fmean(y for _, y in points)
    denominator = sum((x - mean_x) ** 2 for x, _ in points)
    if denominator == 0:
        return None
    return sum((x - mean_x) * (y - mean_y) for x, y in points) / denominator


def safe_prime_subgroup(bits):
    candidate = sympy.nextprime(1 << (bits - 1))
    while not sympy.isprime(2 * candidate + 1):
        candidate = sympy.nextprime(candidate + 1)
    subgroup_order = int(candidate)
    modulus = 2 * subgroup_order + 1
    primitive = int(sympy.primitive_root(modulus))
    generator = pow(primitive, 2, modulus)
    assert pow(generator, subgroup_order, modulus) == 1 and generator != 1
    return modulus, subgroup_order, generator


def rho_step(state, generator, target, modulus, order):
    value, alpha, beta = state
    branch = value % 3
    if branch == 0:
        return value * target % modulus, alpha, (beta + 1) % order
    if branch == 1:
        return value * value % modulus, 2 * alpha % order, 2 * beta % order
    return value * generator % modulus, (alpha + 1) % order, beta


def pollard_rho_log(generator, target, modulus, order, rng, max_restarts=32):
    """Return (logarithm, group multiplications, restarts)."""
    operations = 0
    for restart in range(max_restarts):
        alpha = rng.randrange(order)
        beta = rng.randrange(order)
        value = pow(generator, alpha, modulus) * pow(target, beta, modulus) % modulus
        tortoise = (value, alpha, beta)
        hare = tortoise
        for _ in range(8 * math.isqrt(order) + 100):
            tortoise = rho_step(tortoise, generator, target, modulus, order)
            hare = rho_step(rho_step(hare, generator, target, modulus, order), generator, target, modulus, order)
            operations += 3
            if tortoise[0] != hare[0]:
                continue
            numerator = (tortoise[1] - hare[1]) % order
            denominator = (hare[2] - tortoise[2]) % order
            if denominator:
                logarithm = numerator * pow(denominator, -1, order) % order
                if pow(generator, logarithm, modulus) == target:
                    return logarithm, operations, restart
            break
    raise RuntimeError("Pollard rho exhausted deterministic restarts")


def benchmark_rho(bit_sizes, trials, seed):
    rows = []
    rng = random.Random(seed)
    for bits in bit_sizes:
        modulus, order, generator = safe_prime_subgroup(bits)
        operation_counts, timings = [], []
        for _ in range(trials):
            secret = rng.randrange(1, order)
            target = pow(generator, secret, modulus)
            started = time.perf_counter()
            recovered, operations, _ = pollard_rho_log(
                generator, target, modulus, order, rng
            )
            elapsed = time.perf_counter() - started
            if recovered != secret:
                raise AssertionError("rho returned an incorrect logarithm")
            operation_counts.append(operations)
            timings.append(elapsed)
        rows.append(
            {
                "requested_bits": bits,
                "subgroup_order": order,
                "modulus": modulus,
                "trials": trials,
                "median_group_multiplications": statistics.median(operation_counts),
                "median_seconds": statistics.median(timings),
                "all_logs_verified": True,
            }
        )
    return {
        "model": "Pollard rho in a safe-prime multiplicative subgroup",
        "rows": rows,
        "fitted_exponent_group_multiplications_vs_order": fit_log_slope(
            rows, "subgroup_order", "median_group_multiplications"
        ),
        "fitted_exponent_seconds_vs_order": fit_log_slope(
            rows, "subgroup_order", "median_seconds"
        ),
    }


def klein_line_polynomial(prime, slope, intercept):
    """Coefficients low-to-high of F(x,m*x+b,1) for Klein's quartic.

    F(X,Y,Z)=X^3Y+Y^3Z+Z^3X is smooth away from characteristic 7.
    """
    p, m, b = prime, slope, intercept
    return [
        pow(b, 3, p),
        (3 * m * b * b + 1) % p,
        (3 * m * m * b) % p,
        (b + pow(m, 3, p)) % p,
        m % p,
    ]


def split_roots(coefficients, prime, symbol):
    polynomial = sympy.Poly(list(reversed(coefficients)), symbol, modulus=prime)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SymPyDeprecationWarning)
        unit, factors = sympy.factor_list(polynomial, modulus=prime)
    if sum(factor.degree() * multiplicity for factor, multiplicity in factors) != 4:
        return None
    if any(factor.degree() != 1 for factor, _ in factors):
        return None
    roots = []
    for factor, multiplicity in factors:
        leading, constant = [int(value) % prime for value in factor.all_coeffs()]
        root = -constant * pow(leading, -1, prime) % prime
        roots.extend([root] * multiplicity)
    return tuple(sorted(roots)) if len(roots) == 4 else None


def benchmark_quartic(field_sizes, relation_fraction, seed):
    x = sympy.Symbol("x")
    rows = []
    for prime in field_sizes:
        if not sympy.isprime(prime) or prime in (2, 7):
            raise ValueError("Klein benchmark fields must have prime characteristic other than 2 or 7")
        target_relations = max(8, math.ceil(prime * relation_fraction))
        rng = random.Random(seed ^ prime)
        seen_lines = set()
        factor_base_points = set()
        relation_hash = hashlib.sha256()
        relations = candidates = 0
        started = time.perf_counter()
        while relations < target_relations:
            slope = rng.randrange(1, prime)
            intercept = rng.randrange(prime)
            if (slope, intercept) in seen_lines:
                continue
            seen_lines.add((slope, intercept))
            candidates += 1
            roots = split_roots(
                klein_line_polynomial(prime, slope, intercept), prime, x
            )
            if roots is None:
                continue
            for root in roots:
                y = (slope * root + intercept) % prime
                if (pow(root, 3, prime) * y + pow(y, 3, prime) + root) % prime:
                    raise AssertionError("factor root is not on the Klein quartic")
                factor_base_points.add((root, y))
            relation_hash.update(f"{slope}:{intercept}:{roots};".encode())
            relations += 1
        elapsed = time.perf_counter() - started
        rows.append(
            {
                "field_size_q": prime,
                "target_relations": target_relations,
                "relations_collected": relations,
                "candidate_lines_tested": candidates,
                "candidate_lines_per_relation": candidates / relations,
                "distinct_affine_points_seen": len(factor_base_points),
                "seconds": elapsed,
                "relations_sha256": relation_hash.hexdigest(),
                "all_intersection_points_verified": True,
            }
        )
    return {
        "curve": "Klein quartic X^3*Y + Y^3*Z + Z^3*X = 0",
        "relation_primitive": "factor F(x,m*x+b,1) and retain lines whose four intersections are F_q-rational",
        "relation_target": f"ceil({relation_fraction}*q) raw relations",
        "rows": rows,
        "fitted_exponent_candidate_lines_vs_q": fit_log_slope(
            rows, "field_size_q", "candidate_lines_tested"
        ),
        "fitted_exponent_seconds_vs_q": fit_log_slope(rows, "field_size_q", "seconds"),
    }


def run(rho_bits, rho_trials, quartic_fields, relation_fraction, seed):
    started = time.perf_counter()
    rho = benchmark_rho(rho_bits, rho_trials, seed)
    quartic = benchmark_quartic(quartic_fields, relation_fraction, seed)
    return {
        "format": "hecdlp-toy-empirical-benchmark-v1",
        "seed": seed,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "sympy": sympy.__version__,
        },
        "rho": rho,
        "plane_quartic_relation_collection": quartic,
        "measured_conclusion": (
            "At these toy sizes, real rho logarithms and real split-line quartic relations were computed; "
            "the fitted operation-count slopes may be compared with the modeled 1/2 and 1 exponents."
        ),
        "scope_limits": [
            "not a NIST-size run",
            "rho group is a safe-prime multiplicative subgroup, used as a concrete generic group",
            "quartic benchmark collects raw principal-divisor relations but does not perform rank filtering, sparse linear algebra, or individual-log descent",
            "the two wall-clock columns use different arithmetic primitives and are not direct equivalent-cost comparisons",
            "small-size fitted slopes are descriptive measurements, not asymptotic proofs or cryptographic extrapolations",
        ],
        "total_seconds": time.perf_counter() - started,
    }


def parse_ints(value):
    return [int(item) for item in value.split(",") if item]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rho-bits", default="14,18,22,26,30")
    parser.add_argument("--rho-trials", type=int, default=7)
    parser.add_argument("--quartic-fields", default="101,211,401,809")
    parser.add_argument("--relation-fraction", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=3332026)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run(
        parse_ints(args.rho_bits),
        args.rho_trials,
        parse_ints(args.quartic_fields),
        args.relation_fraction,
        args.seed,
    )
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
