#!/usr/bin/env python3
"""Test norm-ideal Hilbert profiles across random coefficient triples."""

from collections import Counter
import json
from pathlib import Path
from random import Random

from homogeneous_norm_hilbert import homogeneous_hilbert_function


PRIMES = (101, 103, 107)
DIMENSIONS = tuple(range(3, 9))
SAMPLES = 4
SEED = 81_450_771
DETERMINISTIC_COEFFICIENTS = {
    "u": (1, 0, 1),
    "v": (1, 1),
    "w": (1, 0, 0, 1),
}


def add_term(form, exponent, coefficient, prime):
    form[exponent] = (form.get(exponent, 0) + coefficient) % prime


def coefficient_forms(dimension, prime, u, v, w):
    """Coefficients of w*B^2-2*v*B*C-u*C^2 in the chart at infinity."""
    b_count = dimension // 2
    c_count = dimension - b_count
    forms = [{} for _ in range(dimension + 2)]

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


def profile(dimension, prime, u, v, w):
    hilbert, _, _ = homogeneous_hilbert_function(
        coefficient_forms(dimension, prime, u, v, w),
        dimension,
        prime,
    )
    return tuple(hilbert)


def random_coefficients(prime, rng):
    return {
        "u": tuple([rng.randrange(prime) for _ in range(2)]
                   + [rng.randrange(1, prime)]),
        "v": tuple(rng.randrange(prime) for _ in range(2)),
        "w": tuple([rng.randrange(prime) for _ in range(3)]
                   + [rng.randrange(1, prime)]),
    }


def main():
    reference_source = json.loads(
        Path(__file__).with_name("homogeneous_norm_hilbert.json").read_text(
            encoding="utf-8"
        )
    )
    references = {
        panel["projective_section_dimension"]: tuple(
            panel["homogeneous_hilbert_function_through_zero"]
        )
        for panel in reference_source["panels"]
    }
    rng = Random(SEED)
    panels = []
    for prime in PRIMES:
        for dimension in DIMENSIONS:
            random_profiles = []
            for _ in range(SAMPLES):
                item = random_coefficients(prime, rng)
                random_profiles.append(
                    profile(dimension, prime, **item)
                )
            counts = Counter(random_profiles)
            deterministic = profile(
                dimension,
                prime,
                **DETERMINISTIC_COEFFICIENTS,
            )
            reference = references[dimension]
            panels.append({
                "prime": prime,
                "projective_section_dimension": dimension,
                "reference_profile": reference,
                "random_profile_histogram": [
                    {"profile": key, "count": count}
                    for key, count in sorted(counts.items())
                ],
                "all_random_profiles_match_reference": all(
                    value == reference for value in random_profiles
                ),
                "deterministic_profile": deterministic,
                "deterministic_profile_matches_reference": (
                    deterministic == reference
                ),
            })
    result = {
        "seed": SEED,
        "primes": PRIMES,
        "dimensions": DIMENSIONS,
        "random_samples_per_prime_and_dimension": SAMPLES,
        "deterministic_coefficients": DETERMINISTIC_COEFFICIENTS,
        "algorithm_claimed": False,
        "scope": (
            "Exact finite-field Hilbert profiles for independent coefficient "
            "triples in the genus-two norm convolution degree pattern."
        ),
        "all_controls_match_reference": all(
            panel["all_random_profiles_match_reference"]
            and panel["deterministic_profile_matches_reference"]
            for panel in panels
        ),
        "panels": panels,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
