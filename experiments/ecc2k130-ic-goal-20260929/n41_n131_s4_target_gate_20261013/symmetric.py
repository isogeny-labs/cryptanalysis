"""Recover the elementary-symmetric form of the exact S4 polynomial."""

import json
from pathlib import Path

from derive import ONE, add, mul, var

HERE = Path(__file__).resolve().parent


def power(base, exponent):
    result = ONE
    for _ in range(exponent):
        result = mul(result, base)
    return result


def main():
    x = [var(i) for i in range(4)]
    elementary = []
    for size in range(1, 5):
        from itertools import combinations
        elementary.append(add(*(product(x[i] for i in indices)
                                 for indices in combinations(range(4), size))))
    original = frozenset(tuple(row) for row in
                         json.loads((HERE / "resultant.json").read_text())["terms"])
    remainder = original
    expression = []
    while remainder:
        leading = max(remainder)
        assert all(leading[i] >= leading[i + 1] for i in range(3)), leading
        exponents = [leading[i] - leading[i + 1] for i in range(3)] + [leading[3]]
        term = ONE
        for basis, count in zip(elementary, exponents):
            term = mul(term, power(basis, count))
        assert leading in term
        remainder = add(remainder, term)
        expression.append(exponents)
        assert len(expression) <= 1000
    replay = frozenset()
    for exponents in expression:
        term = ONE
        for basis, count in zip(elementary, exponents):
            term = mul(term, power(basis, count))
        replay = add(replay, term)
    assert replay == original
    result = {"status": "EXACT_SYMMETRIC_S4_REPRESENTATION",
              "elementary_variables": ["e1", "e2", "e3", "e4"],
              "terms": expression, "term_count": len(expression),
              "polynomial_term_count": len(original)}
    (HERE / "symmetric_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


def product(values):
    result = ONE
    for value in values:
        result = mul(result, value)
    return result


if __name__ == "__main__":
    main()
