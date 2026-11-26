#!/usr/bin/env python3
"""Verify that redundancy-one RS two-list recovery is modular Subset Sum."""

from itertools import product
import json

from projective_scaling_control import rank_mod


PRIME = 101
ABSCISSAE = (1, 2, 4, 8, 16, 32, 64)
CASES = (
    ((3, 5, 7, 11, 13, 17, 19), 24),
    ((2, 9, 15, 21, 28, 33, 47), 50),
)


def dual_weights(xs, prime):
    out = []
    for index, x in enumerate(xs):
        derivative = 1
        for other_index, other in enumerate(xs):
            if index != other_index:
                derivative = derivative * (x - other) % prime
        out.append(pow(derivative, -1, prime))
    return tuple(out)


def main():
    xs = ABSCISSAE
    m = len(xs)
    dimension = m - 1
    parity = dual_weights(xs, PRIME)
    vandermonde = [
        [pow(x, degree, PRIME) for degree in range(dimension)]
        for x in xs
    ]
    assert rank_mod(vandermonde, PRIME) == dimension
    panels = []
    for weights, target in CASES:
        baseline = [0] * m
        baseline[0] = -target * pow(parity[0], -1, PRIME) % PRIME
        differences = [
            weight * pow(check, -1, PRIME) % PRIME
            for weight, check in zip(weights, parity, strict=True)
        ]
        lists = [
            (base, (base + difference) % PRIME)
            for base, difference in zip(
                baseline, differences, strict=True
            )
        ]
        subset_solutions = []
        recovered_codewords = []
        for choices in product((0, 1), repeat=m):
            word = [
                lists[index][choice]
                for index, choice in enumerate(choices)
            ]
            subset_hit = (
                sum(
                    weight * choice
                    for weight, choice in zip(
                        weights, choices, strict=True
                    )
                )
                - target
            ) % PRIME == 0
            syndrome_zero = sum(
                check * value
                for check, value in zip(parity, word, strict=True)
            ) % PRIME == 0
            augmented = [
                row + [value]
                for row, value in zip(vandermonde, word, strict=True)
            ]
            is_codeword = rank_mod(augmented, PRIME) == dimension
            assert subset_hit == syndrome_zero == is_codeword
            if subset_hit:
                subset_solutions.append(choices)
            if is_codeword:
                recovered_codewords.append(choices)
        assert subset_solutions == recovered_codewords
        panels.append({
            "weights": weights,
            "target": target,
            "sign_assignments": 2 ** m,
            "modular_subset_solutions": len(subset_solutions),
            "rs_list_recovery_solutions": len(recovered_codewords),
            "equivalence_verified": True,
        })

    result = {
        "prime": PRIME,
        "abscissae": xs,
        "length": m,
        "dimension": dimension,
        "redundancy": m - dimension,
        "dual_parity_weights": parity,
        "panels": panels,
        "all_equivalences_verified": all(
            panel["equivalence_verified"] for panel in panels
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
