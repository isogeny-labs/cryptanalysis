#!/usr/bin/env python3
"""Parameter ledger for folded recovery of split-fiber rational sections."""

import json
from math import ceil, log2, sqrt


PRIME_BITS = (64, 128, 256)
MAX_MULTIPLICITY = 48


def ordinary_interpolation_ratio(slots, b_degree, c_degree):
    best = None
    for multiplicity in range(1, MAX_MULTIPLICITY + 1):
        weighted_limit = slots * multiplicity - 1
        for y_degree in range(0, 2 * multiplicity + 2):
            monomials = sum(
                max(
                    0,
                    weighted_limit
                    - (j * c_degree + (y_degree - j) * b_degree)
                    + 1,
                )
                for j in range(y_degree + 1)
            )
            conditions = slots * multiplicity * (multiplicity + 1)
            ratio = monomials / conditions
            candidate = (ratio, multiplicity, y_degree, monomials, conditions)
            if best is None or candidate > best:
                best = candidate
    ratio, multiplicity, y_degree, monomials, conditions = best
    return {
        "maximum_monomial_to_condition_ratio": ratio,
        "multiplicity_at_maximum": multiplicity,
        "y_degree_at_maximum": y_degree,
        "monomials_at_maximum": monomials,
        "double_branch_conditions_at_maximum": conditions,
        "interpolation_system_overdetermined": monomials <= conditions,
    }


def row(genus, prime_bits):
    excess_bits = ceil(sqrt(prime_bits))
    slots = genus * prime_bits + excess_bits
    section_parameters = slots - genus
    b_degree = (section_parameters - 1) // 2
    c_degree = section_parameters // 2
    folding = ceil(sqrt(prime_bits))
    blocks = ceil(slots / folding)
    block_list_size = 2**folding
    rate = (slots - genus) / slots
    zero_error_slack = 1 - rate
    required_folding = ceil(block_list_size / zero_error_slack**2)
    result = {
        "genus": genus,
        "prime_bits": prime_bits,
        "slots": slots,
        "section_parameters": section_parameters,
        "expected_output_log2": slots - genus * prime_bits,
        "expected_output_exponent_in_p": (
            slots - genus * prime_bits
        ) / prime_bits,
        "folding_parameter": folding,
        "folded_blocks": blocks,
        "cartesian_branch_list_size_per_block": block_list_size,
        "explicit_folded_input_log2_upper_bound": (
            folding + log2(blocks)
        ),
        "explicit_folded_input_exponent_in_p": (
            folding + log2(blocks)
        ) / prime_bits,
        "rational_code_rate": rate,
        "maximum_zero_error_slack": zero_error_slack,
        "standard_frs_required_folding_lower_bound_proxy": required_folding,
        "log2_standard_required_folding_proxy": log2(required_folding),
        "standard_frs_folding_condition_met": folding >= required_folding,
    }
    result.update(ordinary_interpolation_ratio(slots, b_degree, c_degree))
    return result


def main():
    result = {
        "model": (
            "two rational-section branches per split fiber; blocks of f "
            "evaluations expose Cartesian lists of size 2^f"
        ),
        "oversampling": "m=g log2(p)+ceil(sqrt(log2(p)))",
        "standard_frs_condition": (
            "capacity-level list recovery requires folding "
            "Omega(list_size/slack^2); constants suppressed in the proxy"
        ),
        "algorithm_claimed": False,
        "rows": [
            row(genus, bits)
            for genus in range(2, 8)
            for bits in PRIME_BITS
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
