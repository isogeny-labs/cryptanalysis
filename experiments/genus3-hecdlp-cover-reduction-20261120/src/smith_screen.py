#!/usr/bin/env python3
"""Eligibility and cost screen for the Smith genus-3 DLP reduction.

For a genus-3 hyperelliptic curve H: y^2=f(x), deg(f)=7 or 8, the eight
Weierstrass points carry the Frobenius permutation encoded by the degrees of
the irreducible factors of the homogenized degree-8 polynomial. A
Frobenius-stable perfect matching gives a rational tractable (2,2,2) kernel.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import platform
import sys
import time
from collections import Counter
from fractions import Fraction
from pathlib import Path

import sympy


def integer_partitions(total: int, maximum: int | None = None):
    if total == 0:
        yield ()
        return
    if maximum is None or maximum > total:
        maximum = total
    for first in range(maximum, 0, -1):
        for rest in integer_partitions(total - first, first):
            yield (first,) + rest


def perfect_matchings(items):
    items = tuple(items)
    if not items:
        yield frozenset()
        return
    first = items[0]
    for i in range(1, len(items)):
        second = items[i]
        remainder = items[1:i] + items[i + 1 :]
        pair = frozenset((first, second))
        for matching in perfect_matchings(remainder):
            yield frozenset((pair,)) | matching


MATCHINGS_8 = tuple(perfect_matchings(range(8)))


def cycle_permutation(pattern):
    if sum(pattern) != 8 or any(part <= 0 for part in pattern):
        raise ValueError("positive factor degrees must sum to eight")
    permutation = list(range(8))
    start = 0
    for length in pattern:
        cycle = list(range(start, start + length))
        for left, right in zip(cycle, cycle[1:] + cycle[:1]):
            permutation[left] = right
        start += length
    return tuple(permutation)


def transport_pair(pair, permutation):
    return frozenset(permutation[i] for i in pair)


def invariant_matching(matching, permutation):
    return frozenset(transport_pair(pair, permutation) for pair in matching) == matching


def tractable_count(pattern):
    permutation = cycle_permutation(pattern)
    return sum(invariant_matching(matching, permutation) for matching in MATCHINGS_8)


def stable_matchings(pattern):
    permutation = cycle_permutation(pattern)
    return [
        sorted([sorted(pair) for pair in matching])
        for matching in MATCHINGS_8
        if invariant_matching(matching, permutation)
    ]


def cycle_type_weight(pattern):
    """Asymptotic probability of this squarefree degree-8 factorization type."""
    counts = Counter(pattern)
    denominator = 1
    for degree, multiplicity in counts.items():
        denominator *= degree**multiplicity * math.factorial(multiplicity)
    return Fraction(1, denominator)


def conditional_isogeny_success(count):
    """Smith's modeled success, under the paper's four hypotheses."""
    return Fraction(1, 1) - Fraction(3, 4) ** count


def all_pattern_rows():
    rows = []
    for pattern in integer_partitions(8):
        count = tractable_count(pattern)
        weight = cycle_type_weight(pattern)
        success = conditional_isogeny_success(count)
        rows.append(
            {
                "factor_degrees": list(pattern),
                "tractable_kernels": count,
                "cycle_type_weight": {"numerator": weight.numerator, "denominator": weight.denominator},
                "conditional_success": {
                    "numerator": success.numerator,
                    "denominator": success.denominator,
                    "decimal": float(success),
                },
            }
        )
    return rows


def asymptotic_success():
    total = Fraction(0, 1)
    weight_sum = Fraction(0, 1)
    for row in all_pattern_rows():
        weight = Fraction(row["cycle_type_weight"]["numerator"], row["cycle_type_weight"]["denominator"])
        success = Fraction(row["conditional_success"]["numerator"], row["conditional_success"]["denominator"])
        total += weight * success
        weight_sum += weight
    assert weight_sum == 1
    return total


def cost_model(q_bits):
    return {
        "q_bits": q_bits,
        "pollard_on_order_q_cubed_log2_scale": 1.5 * q_bits,
        "direct_hyperelliptic_genus3_log2_scale": (4 / 3) * q_bits,
        "plane_quartic_diem_log2_scale": q_bits,
        "hyperelliptic_to_plane_quartic_exponent_saving_bits": q_bits / 3,
        "pollard_to_plane_quartic_exponent_saving_bits": q_bits / 2,
        "label": "published soft-O exponent model; constants, polylogs, construction, linear-algebra engineering, and descent are not measured",
    }


def factorization_pattern(prime, coefficients_high_to_low):
    """Factor a squarefree degree-7/8 hyperelliptic polynomial over F_p.

    A degree-7 affine model has one additional rational Weierstrass point at
    infinity, so a degree-one part is appended to the homogeneous pattern.
    """
    if prime <= 3 or not sympy.isprime(prime):
        raise ValueError("Smith's construction requires a prime characteristic greater than three")
    x = sympy.symbols("x")
    coefficients = [int(c) % prime for c in coefficients_high_to_low]
    while coefficients and coefficients[0] == 0:
        coefficients.pop(0)
    degree = len(coefficients) - 1
    if degree not in (7, 8):
        raise ValueError("a genus-3 hyperelliptic model must have degree 7 or 8")
    polynomial = sympy.Poly.from_list(coefficients, gens=x, modulus=prime)
    if sympy.gcd(polynomial, polynomial.diff()).degree() != 0:
        raise ValueError("hyperelliptic polynomial must be squarefree")
    _, factors = sympy.factor_list(polynomial)
    degrees = []
    for factor, multiplicity in factors:
        if multiplicity != 1:
            raise ValueError("hyperelliptic polynomial must be squarefree")
        degrees.append(factor.degree())
    if degree == 7:
        degrees.append(1)
    return tuple(sorted(degrees, reverse=True))


def environment():
    return {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": sys.version,
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
    }


def build_result(pattern=None, q_bits=85.0, polynomial_input=None):
    success = asymptotic_success()
    result = {
        "format": "hecdlp-cover-smith-screen-v1",
        "mechanism": "genus-3 hyperelliptic Jacobian --(2,2,2)--> non-hyperelliptic plane-quartic Jacobian",
        "scope": "odd characteristic greater than 3; no DLP solving",
        "primary_source": {
            "author": "Benjamin Smith",
            "title": "Isogenies and the Discrete Logarithm Problem in Jacobians of Genus 3 Hyperelliptic Curves",
            "arxiv": "https://arxiv.org/abs/0806.2995",
        },
        "perfect_matching_count": len(MATCHINGS_8),
        "pattern_rows": all_pattern_rows(),
        "asymptotic_random_curve_success": {
            "numerator": success.numerator,
            "denominator": success.denominator,
            "decimal": float(success),
        },
        "cost_model": cost_model(q_bits),
        "subgroup_certificate": {
            "kernel_order": 8,
            "kernel_exponent": 2,
            "odd_order_target_intersection": "trivial",
            "polarized_dual_identity": "phi^dagger o phi = [2]",
            "recovery": "[2^(-1) mod n] o phi^dagger on an odd-order subgroup",
        },
        "environment": environment(),
    }
    if pattern is not None:
        pattern = tuple(sorted(pattern, reverse=True))
        count = tractable_count(pattern)
        result["selected_pattern"] = {
            "factor_degrees": list(pattern),
            "tractable_kernels": count,
            "matchings": stable_matchings(pattern),
            "modeled_conditional_success": float(conditional_isogeny_success(count)),
        }
    if polynomial_input is not None:
        prime, coefficients = polynomial_input
        observed = factorization_pattern(prime, coefficients)
        count = tractable_count(observed)
        result["polynomial_screen"] = {
            "prime": prime,
            "coefficients_high_to_low": coefficients,
            "homogeneous_factor_degrees": list(observed),
            "tractable_kernels": count,
            "matchings": stable_matchings(observed),
            "modeled_conditional_success": float(conditional_isogeny_success(count)),
        }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--degrees", help="comma-separated irreducible-factor degrees summing to 8")
    parser.add_argument("--prime", type=int, help="odd prime for a supplied degree-7/8 polynomial")
    parser.add_argument("--poly", help="comma-separated polynomial coefficients, highest degree first")
    parser.add_argument("--q-bits", type=float, default=85.0)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    pattern = None if args.degrees is None else [int(x) for x in args.degrees.split(",")]
    if (args.prime is None) != (args.poly is None):
        parser.error("--prime and --poly must be supplied together")
    polynomial_input = None
    if args.prime is not None:
        polynomial_input = (args.prime, [int(x) for x in args.poly.split(",")])
    result = build_result(pattern=pattern, q_bits=args.q_bits, polynomial_input=polynomial_input)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
