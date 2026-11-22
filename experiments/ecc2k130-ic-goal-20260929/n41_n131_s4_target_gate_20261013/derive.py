"""Expand the adjacent-S3 resultant in GF(2)[a,b,c,t]."""

import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ZERO = frozenset()
ONE = frozenset({(0, 0, 0, 0)})


def var(index):
    exponent = [0, 0, 0, 0]
    exponent[index] = 1
    return frozenset({tuple(exponent)})


def add(*polynomials):
    out = set()
    for polynomial in polynomials:
        out.symmetric_difference_update(polynomial)
    return frozenset(out)


def mul(left, right):
    out = set()
    for a in left:
        for b in right:
            exponent = tuple(x + y for x, y in zip(a, b))
            if exponent in out:
                out.remove(exponent)
            else:
                out.add(exponent)
    return frozenset(out)


def square(poly):
    return frozenset(tuple(2 * value for value in exponent) for exponent in poly)


def s3_coefficients(x, y):
    product = mul(x, y)
    return add(ONE, square(product)), product, add(square(x), square(y))


def evaluate(poly, values, multiply):
    out = 0
    for powers in poly:
        term = 1
        for value, exponent in zip(values, powers):
            for _ in range(exponent):
                term = multiply(term, value)
        out ^= term
    return out


def main():
    a, b, c, t = [var(index) for index in range(4)]
    A, B, C = s3_coefficients(a, b)
    D, E, F = s3_coefficients(c, t)
    M = add(mul(A, F), mul(D, C))
    L = add(mul(A, E), mul(D, B))
    K = add(mul(B, F), mul(E, C))
    resultant = add(square(M), mul(L, K))
    terms = sorted(resultant)
    assert terms
    result = {"status": "EXACT_RECIPROCAL_S4_RESULTANT",
              "variables": ["a", "b", "c", "t"],
              "formula": "M^2+L*K with M=A*F+D*C, L=A*E+D*B, K=B*F+E*C",
              "s3_coefficients": "A=1+(ab)^2, B=ab, C=a^2+b^2; D=1+(ct)^2, E=ct, F=c^2+t^2",
              "terms": [list(term) for term in terms],
              "term_count": len(terms),
              "total_degree": max(sum(term) for term in terms),
              "degrees_by_variable": [max(term[i] for term in terms) for i in range(4)],
              "degree_histogram": dict(sorted(Counter(sum(term) for term in terms).items()))}
    (HERE / "resultant.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("status", "term_count", "total_degree",
                                                   "degrees_by_variable", "degree_histogram")},
                     sort_keys=True))


if __name__ == "__main__":
    main()
