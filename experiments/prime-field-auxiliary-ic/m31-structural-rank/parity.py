"""Replay binary stopping rows and the primitive integral dependency of each archive."""
import csv
from fractions import Fraction
import json
import math
import sys

from audit import ORDER, archive, coefficients


def binary_dependencies(rows):
    pivots = {}
    dependent = []
    for index, row in enumerate(rows, 1):
        bits = sum(1 << col for col, value in row.items() if value % 2)
        while bits:
            col = bits.bit_length() - 1
            if col not in pivots:
                pivots[col] = bits
                break
            bits ^= pivots[col]
        if not bits:
            dependent.append(index)
    return dependent


def primitive_weights(rows):
    # Keep the elementary row operations. Replaying them backwards from
    # the final zero row yields the dependency in the original row order.
    pivots = {}
    history = []
    for index, row in enumerate(rows):
        vector = {col: Fraction(value) for col, value in row.items()}
        operations = []
        divisor = 1
        while vector:
            col = min(vector)
            value = vector[col]
            if col not in pivots:
                divisor = value
                pivots[col] = (index, {j: x / divisor for j, x in vector.items()})
                break
            prior, pivot = pivots[col]
            operations.append((prior, value))
            for j, x in pivot.items():
                updated = vector.get(j, 0) - value * x
                if updated:
                    vector[j] = updated
                else:
                    vector.pop(j, None)
        assert bool(vector) == (index < len(rows) - 1)
        history.append((divisor, operations))

    weights = [Fraction(0)] * len(rows)
    weights[-1] = Fraction(1)
    for i in reversed(range(len(rows))):
        divisor, operations = history[i]
        weights[i] /= divisor
        for prior, value in operations:
            weights[prior] -= weights[i] * value
    denominator = math.lcm(*(w.denominator for w in weights))
    result = [int(w * denominator) for w in weights]
    assert math.gcd(*result) == 1
    balances = [0] * 500
    for row, weight in zip(rows, result):
        for col, value in row.items():
            balances[col] += weight * value
    assert not any(balances)
    return result


def main():
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["seed", "method", "final_row", "binary_dependent_rows",
                     "odd_weight_rows", "last_odd_weight_row", "final_weight_v2"])
    for seed in range(3):
        for method in ("auxiliary", "plain"):
            folder = f"{method}/seed{seed}"
            rows = [coefficients(json.loads(s)) for s in archive(folder + "/relations.jsonl").splitlines()]
            weights = primitive_weights(rows)
            archived = json.loads(archive(folder + "/certificate.json"))["weights"]
            assert len(weights) == len(archived)
            assert archived[-1] % ORDER and weights[-1] % ORDER
            assert all((w * archived[-1] - a * weights[-1]) % ORDER == 0
                       for w, a in zip(weights, archived))
            odd = [i for i, w in enumerate(weights, 1) if w % 2]
            dependencies = binary_dependencies(rows)
            assert odd[-1] in dependencies
            final = weights[-1]
            writer.writerow([seed, method, len(rows), " ".join(map(str, dependencies)),
                             len(odd), odd[-1], (final & -final).bit_length() - 1])


if __name__ == "__main__":
    main()
