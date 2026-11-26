#!/usr/bin/env python3
"""Ledger for lifting fixed-genus DLPs to growing-genus covers."""

import json
from math import ceil, log, log2, sqrt


PRIME_BITS = (64, 128, 256)
COVER_DEGREES = (2, 4, 8, 16, 32)


def factor_base_bits(prime_bits):
    """A representative p^o(1) base: exp(sqrt(log p log log p))."""
    natural_log_p = prime_bits * log(2)
    return sqrt(natural_log_p * log(natural_log_p)) / log(2)


def row(genus, prime_bits, cover_degree):
    lifted_genus = cover_degree * (genus - 1) + 1
    base_bits = factor_base_bits(prime_bits)
    lifted_base_bits = base_bits + log2(cover_degree)
    source_arity = ceil(genus * prime_bits / base_bits)
    ambient_arity = ceil(lifted_genus * prime_bits / lifted_base_bits)
    natural_log_p = prime_bits * log(2)
    known_bound_exponent_proxy = 1 + sqrt(
        lifted_genus * log(2 * lifted_genus) / natural_log_p
    )
    return {
        "source_genus": genus,
        "prime_bits": prime_bits,
        "cover_degree": cover_degree,
        "lifted_genus": lifted_genus,
        "subexponential_source_base_log2": base_bits,
        "all_lifts_base_log2": lifted_base_bits,
        "source_coverage_arity": source_arity,
        "ambient_cover_coverage_arity": ambient_arity,
        "prym_dimension": lifted_genus - genus,
        "random_ambient_sum_image_probability_exponent_in_p": -(
            lifted_genus - genus
        ),
        "known_growing_genus_bound_exponent_proxy_in_p": (
            known_bound_exponent_proxy
        ),
        "small_place_setup_exponent_lower_bound_in_p": 1,
    }


def main():
    result = {
        "model": (
            "degree-n unramified cover: g'=n(g-1)+1; all n lifts of a "
            "representative p^o(1) source factor base"
        ),
        "known_bound": (
            "exp(O(log p + sqrt(g' log p log(2g')))); the reported proxy "
            "divides the displayed exponent by log p and suppresses constants"
        ),
        "algorithm_claimed": False,
        "rows": [
            row(genus, bits, degree)
            for genus in range(2, 8)
            for bits in PRIME_BITS
            for degree in COVER_DEGREES
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
