#!/usr/bin/env python3
"""Empirical signed-transfer and dual-recovery control on toy 2-isogenies.

This is a dimension-one control for the map/dual identities required by the
genus-three project.  It does not supply the missing signed P-224 map.
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import statistics
import sys
import time
from pathlib import Path

import sympy


PROFILES = (
    # p, a, b, #E, large odd prime subgroup order
    (1009, 1, 5, 1004, 251),
    (1013, 1, 2, 1018, 509),
    (1019, 1, 4, 1004, 251),
    (5003, 3, 1, 4916, 1229),
    (10007, 4, 5, 10078, 5039),
    (20011, 1, 2, 20198, 10099),
)


def on_curve(point, prime, a, b):
    if point is None:
        return True
    x, y = point
    return (y * y - x**3 - a * x * x - b * x) % prime == 0


def add(left, right, prime, a, b):
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    if x1 == x2 and (y1 + y2) % prime == 0:
        return None
    if left == right:
        slope = (3 * x1 * x1 + 2 * a * x1 + b) * pow(2 * y1, -1, prime) % prime
    else:
        slope = (y2 - y1) * pow(x2 - x1, -1, prime) % prime
    x3 = (slope * slope - a - x1 - x2) % prime
    y3 = (slope * (x1 - x3) - y1) % prime
    return x3, y3


def scalar_mul(scalar, point, prime, a, b):
    result = None
    while scalar:
        if scalar & 1:
            result = add(result, point, prime, a, b)
        point = add(point, point, prime, a, b)
        scalar >>= 1
    return result


def quotient_parameters(prime, a, b):
    return (-2 * a) % prime, (a * a - 4 * b) % prime


def isogeny(point, prime, a, b):
    """2-isogeny with kernel {O,(0,0)}."""
    if point is None or point == (0, 0):
        return None
    x, y = point
    return (
        (x + a + b * pow(x, -1, prime)) % prime,
        y * (1 - b * pow(x * x, -1, prime)) % prime,
    )


def dual_isogeny(point, prime, a, b):
    """Polarized dual, including the E'' -> E scaling isomorphism."""
    if point is None or point == (0, 0):
        return None
    x, y = point
    c = (a * a - 4 * b) % prime
    x_double = (x - 2 * a + c * pow(x, -1, prime)) % prime
    y_double = y * (1 - c * pow(x * x, -1, prime)) % prime
    return x_double * pow(4, -1, prime) % prime, y_double * pow(8, -1, prime) % prime


def subgroup_generator(prime, a, b, group_order, subgroup_order):
    cofactor = group_order // subgroup_order
    for x in range(1, prime):
        rhs = (x**3 + a * x * x + b * x) % prime
        roots = sympy.sqrt_mod(rhs, prime, all_roots=True)
        for y in roots:
            candidate = scalar_mul(cofactor, (x, int(y)), prime, a, b)
            if candidate is not None and scalar_mul(subgroup_order, candidate, prime, a, b) is None:
                return candidate
    raise RuntimeError("failed to find subgroup generator")


def benchmark_profile(profile, seed, repetitions):
    prime, a, b, group_order, subgroup_order = profile
    quotient_a, quotient_b = quotient_parameters(prime, a, b)
    generator = subgroup_generator(prime, a, b, group_order, subgroup_order)
    rng = random.Random(seed ^ prime)
    secret = rng.randrange(1, subgroup_order)
    target = scalar_mul(secret, generator, prime, a, b)
    image_generator = isogeny(generator, prime, a, b)
    image_target = isogeny(target, prime, a, b)
    inverse_two = pow(2, -1, subgroup_order)

    identities = {
        "source_generator_on_curve": on_curve(generator, prime, a, b),
        "images_on_quotient_curve": on_curve(image_generator, prime, quotient_a, quotient_b)
        and on_curve(image_target, prime, quotient_a, quotient_b),
        "dlog_preserved": image_target
        == scalar_mul(secret, image_generator, prime, quotient_a, quotient_b),
        "dual_composition_is_2": dual_isogeny(image_generator, prime, a, b)
        == scalar_mul(2, generator, prime, a, b),
        "signed_recovery": scalar_mul(
            inverse_two,
            dual_isogeny(image_generator, prime, a, b),
            prime,
            a,
            b,
        )
        == generator,
    }
    if not all(identities.values()):
        raise AssertionError("signed isogeny control failed")

    transfer_samples, recovery_samples = [], []
    point = generator
    for _ in range(repetitions):
        started = time.perf_counter_ns()
        image = isogeny(point, prime, a, b)
        transfer_samples.append(time.perf_counter_ns() - started)
        started = time.perf_counter_ns()
        recovered = scalar_mul(
            inverse_two, dual_isogeny(image, prime, a, b), prime, a, b
        )
        recovery_samples.append(time.perf_counter_ns() - started)
        if recovered != point:
            raise AssertionError("timed signed recovery failed")
        point = add(point, generator, prime, a, b)
        if point is None:
            point = generator
    return {
        "field_prime": prime,
        "curve": f"y^2=x^3+{a}*x^2+{b}*x",
        "quotient_curve": f"y^2=x^3+{quotient_a}*x^2+{quotient_b}*x (coefficients mod p)",
        "group_order": group_order,
        "subgroup_order": subgroup_order,
        "secret": secret,
        "identities": identities,
        "repetitions": repetitions,
        "median_transfer_nanoseconds": statistics.median(transfer_samples),
        "median_dual_recovery_nanoseconds": statistics.median(recovery_samples),
    }


def run(seed=2333, repetitions=2000):
    started = time.perf_counter()
    rows = [benchmark_profile(profile, seed, repetitions) for profile in PROFILES]
    return {
        "format": "signed-isogeny-transfer-control-v1",
        "seed": seed,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "sympy": sympy.__version__,
        },
        "map": "explicit rational 2-isogeny with kernel {O,(0,0)}",
        "dual_identity": "phi_dual(phi(P))=[2]P",
        "recovery": "[2^(-1) mod r] phi_dual on each odd prime-order subgroup",
        "rows": rows,
        "all_checks_pass": all(
            all(row["identities"].values()) for row in rows
        ),
        "scope": {
            "measured": "signed point transfer, preserved DLP scalar, dual composition, and recovery",
            "analogue_only": "dimension-one 2-isogenies over toy prime fields",
            "not_measured": "the missing signed P-224 E^3-to-J_C map or its (3,3,3) dual",
        },
        "total_seconds": time.perf_counter() - started,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=2333)
    parser.add_argument("--repetitions", type=int, default=2000)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run(args.seed, args.repetitions)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
