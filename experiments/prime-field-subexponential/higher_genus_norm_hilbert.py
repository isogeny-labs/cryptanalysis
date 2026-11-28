#!/usr/bin/env python3
"""Measure homogeneous norm Hilbert profiles in genera three through seven."""

from collections import Counter
import json
from math import comb, log2
from random import Random

from homogeneous_norm_hilbert import homogeneous_hilbert_function
from norm_hilbert_universality import add_term
from toy_jacobian import PrimePolynomials


PRIMES = (101, 103)
GENERA = tuple(range(3, 8))
DIMENSIONS = tuple(range(3, 9))
SAMPLES = 2
SEED = 73_004_119
MODEL_DIMENSIONS = (32, 64, 128, 256)


def coefficient_forms(dimension, genus, prime, u, v, w):
    """Quadratic leading coefficients after fixing the top section term."""
    b_count = dimension // 2
    c_count = dimension - b_count
    forms = [{} for _ in range(dimension + genus)]
    for shift, coefficient in enumerate(w):
        for left in range(b_count):
            for right in range(b_count):
                exponent = [0] * dimension
                exponent[left] += 1
                exponent[right] += 1
                add_term(
                    forms[shift + left + right],
                    tuple(exponent),
                    coefficient,
                    prime,
                )
    for shift, coefficient in enumerate(v):
        for left in range(b_count):
            for right in range(c_count):
                exponent = [0] * dimension
                exponent[left] += 1
                exponent[b_count + right] += 1
                add_term(
                    forms[shift + left + right],
                    tuple(exponent),
                    -2 * coefficient,
                    prime,
                )
    for shift, coefficient in enumerate(u):
        for left in range(c_count):
            for right in range(c_count):
                exponent = [0] * dimension
                exponent[b_count + left] += 1
                exponent[b_count + right] += 1
                add_term(
                    forms[shift + left + right],
                    tuple(exponent),
                    -coefficient,
                    prime,
                )
    return [
        {monomial: value for monomial, value in form.items() if value}
        for form in forms
    ]


def random_curve_coefficients(genus, prime, rng):
    poly = PrimePolynomials(prime)
    while True:
        u = tuple(
            [rng.randrange(prime) for _ in range(genus)]
            + [rng.randrange(1, prime)]
        )
        v = tuple(rng.randrange(prime) for _ in range(genus))
        w = tuple(
            [rng.randrange(prime) for _ in range(genus + 1)]
            + [rng.randrange(1, prime)]
        )
        f = poly.add(poly.mul(v, v), poly.mul(u, w))
        derivative = poly.canonical(
            index * value
            for index, value in enumerate(f)
            if index
        )
        if (
            len(f) == 2 * genus + 2
            and poly.xgcd(f, derivative)[0] == (1,)
        ):
            return {"u": u, "v": v, "w": w}


def semiregular_profile(dimension, genus):
    values = []
    for degree in range(2 * dimension + 3):
        value = sum(
            (-1) ** index
            * comb(dimension + genus, index)
            * comb(
                dimension + degree - 2 * index - 1,
                dimension - 1,
            )
            for index in range(degree // 2 + 1)
        )
        if value <= 0:
            return tuple(values + [0])
        values.append(value)
    raise AssertionError("semi-regular series did not truncate")


def at_least_model(profile, model):
    length = max(len(profile), len(model))
    actual = tuple(profile) + (0,) * (length - len(profile))
    predicted = tuple(model) + (0,) * (length - len(model))
    return all(left >= right for left, right in zip(actual, predicted))


def exact_panels(rng):
    observations = {
        (genus, dimension): []
        for genus in GENERA
        for dimension in DIMENSIONS
    }
    for prime in PRIMES:
        for genus in GENERA:
            for _ in range(SAMPLES):
                coefficients = random_curve_coefficients(genus, prime, rng)
                for dimension in DIMENSIONS:
                    forms = coefficient_forms(
                        dimension,
                        genus,
                        prime,
                        **coefficients,
                    )
                    hilbert, _, _ = homogeneous_hilbert_function(
                        forms,
                        dimension,
                        prime,
                    )
                    observations[(genus, dimension)].append(tuple(hilbert))

    panels = []
    for genus in GENERA:
        for dimension in DIMENSIONS:
            profiles = observations[(genus, dimension)]
            model = semiregular_profile(dimension, genus)
            counts = Counter(profiles)
            panels.append({
                "genus": genus,
                "projective_section_dimension": dimension,
                "quadratic_norm_coefficients": dimension + genus,
                "semi_regular_profile": model,
                "profile_histogram": [
                    {"profile": profile, "count": count}
                    for profile, count in sorted(counts.items())
                ],
                "all_profiles_match": len(counts) == 1,
                "all_profiles_coefficientwise_at_least_model": all(
                    at_least_model(profile, model) for profile in profiles
                ),
            })
    return panels


def model_panel(genus, dimension):
    profile = semiregular_profile(dimension, genus)[:-1]
    return {
        "genus": genus,
        "variables": dimension,
        "last_positive_degree": len(profile) - 1,
        "log2_quotient_length_per_variable": (
            log2(sum(profile)) / dimension
        ),
    }


def main():
    rng = Random(SEED)
    panels = exact_panels(rng)
    result = {
        "primes": PRIMES,
        "genera": GENERA,
        "dimensions": DIMENSIONS,
        "samples_per_prime_genus": SAMPLES,
        "seed": SEED,
        "algorithm_claimed": False,
        "scope": (
            "Exact homogeneous norm Hilbert profiles for random valid "
            "prime-field curves in genera three through seven."
        ),
        "all_random_profiles_stable": all(
            panel["all_profiles_match"] for panel in panels
        ),
        "all_profiles_coefficientwise_at_least_semiregular_model": all(
            panel["all_profiles_coefficientwise_at_least_model"]
            for panel in panels
        ),
        "exact_panels": panels,
        "semi_regular_model_only": [
            model_panel(genus, dimension)
            for genus in range(2, 8)
            for dimension in MODEL_DIMENSIONS
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
