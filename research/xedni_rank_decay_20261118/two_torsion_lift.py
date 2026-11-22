#!/usr/bin/env python3
"""Exact Cheon--Lee--Hahn--Chee two-torsion lift identities.

This module verifies the one-parameter construction in section 4 of
"Elliptic Curve Discrete Logarithms and Wieferich Primes".  It does not
compute a Mordell--Weil rank or certify a useful relation.
"""

from __future__ import annotations

import math
from typing import Any

from prime_manifest import is_prime_u32


SCHEMA = "xedni-two-torsion-lift/v1"


def _plain_int(name: str, value: Any) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a plain integer")
    return value


def _source_on_curve(x: int, y: int, a: int, b: int, prime: int) -> bool:
    return (y * y - x * (x * x + a * x + b)) % prime == 0


def _gamma_delta(t: int, prime: int, difference: int) -> tuple[int, int]:
    gamma = pow(t * prime, -1, difference)
    numerator = 1 - gamma * t * prime
    if numerator % difference:
        raise ArithmeticError("gamma did not produce an integral delta")
    return gamma, numerator // difference


def build_lift(
    *,
    prime: int,
    source_a: int,
    source_b: int,
    t1: int,
    t2: int,
    b1: int,
    b2: int,
    parameter_n: int,
) -> dict[str, Any]:
    """Construct and exactly replay one member of the published family.

    The source points are
      Pbar = (t1^2, t1*b1), Qbar = (-t2^2, t2*b2) modulo ``prime``.
    The returned integral curve is ``y^2 = x(x^2 + A*x + B)``.
    """

    prime = _plain_int("prime", prime)
    source_a = _plain_int("source_a", source_a)
    source_b = _plain_int("source_b", source_b)
    t1 = _plain_int("t1", t1)
    t2 = _plain_int("t2", t2)
    b1 = _plain_int("b1", b1)
    b2 = _plain_int("b2", b2)
    parameter_n = _plain_int("parameter_n", parameter_n)
    if prime >= 2**32 or not is_prime_u32(prime) or prime == 2:
        raise ValueError("prime must be an odd unsigned 32-bit prime")
    if not t1 or not t2 or t1 % 2 == 0 or t2 % 2 == 0:
        raise ValueError("t1 and t2 must be nonzero odd integers")
    if math.gcd(t1, t2) != 1:
        raise ValueError("t1 and t2 must be coprime")

    difference = t1 * t1 + t2 * t2
    if math.gcd(t1 * prime, difference) != 1 or math.gcd(
        t2 * prime, difference
    ) != 1:
        raise ValueError("the published gamma inverses do not exist")

    source_x1 = t1 * t1 % prime
    source_y1 = t1 * b1 % prime
    source_x2 = -(t2 * t2) % prime
    source_y2 = t2 * b2 % prime
    if source_x1 == source_x2:
        raise ValueError("source points must have distinct x-coordinates")
    for label, x, y in (
        ("Pbar", source_x1, source_y1),
        ("Qbar", source_x2, source_y2),
    ):
        if not _source_on_curve(x, y, source_a, source_b, prime):
            raise ValueError(f"{label} is not on the source curve")

    gamma1, delta1 = _gamma_delta(t1, prime, difference)
    gamma2, delta2 = _gamma_delta(t2, prime, difference)
    s1 = b1 * delta1
    s2 = b2 * delta2
    pn = prime * parameter_n

    lift_a = (
        pn * pn
        + 2 * (s1 * t1 + s2 * t2) * pn
        + (s1 * s1 + s2 * s2) * difference
        - (t1 * t1 - t2 * t2)
    )
    lift_b = (
        2 * (s1 * t2 - s2 * t1) * t1 * t2 * pn
        + (s1 * s1 * t2 * t2 - s2 * s2 * t1 * t1) * difference
        - t1 * t1 * t2 * t2
    )
    lift_x1 = t1 * t1
    lift_x2 = -(t2 * t2)
    lift_y1 = t1 * (s1 * difference + t1 * pn)
    lift_y2 = t2 * (s2 * difference + t2 * pn)

    factor_plus = (
        pn * pn
        + 2 * (s1 * t1 + s2 * t2 + t1) * pn
        + (s1 * s1 + s2 * s2 + 1 + 2 * s1) * difference
    )
    factor_minus = (
        pn * pn
        + 2 * (s1 * t1 + s2 * t2 - t1) * pn
        + (s1 * s1 + s2 * s2 + 1 - 2 * s1) * difference
    )
    discriminant_term = lift_a * lift_a - 4 * lift_b

    if lift_y1 * lift_y1 != lift_x1 * (
        lift_x1 * lift_x1 + lift_a * lift_x1 + lift_b
    ):
        raise ArithmeticError("first lifted point failed the integral curve equation")
    if lift_y2 * lift_y2 != lift_x2 * (
        lift_x2 * lift_x2 + lift_a * lift_x2 + lift_b
    ):
        raise ArithmeticError("second lifted point failed the integral curve equation")
    if (lift_a - source_a) % prime or (lift_b - source_b) % prime:
        raise ArithmeticError("lifted curve did not reduce to the source curve")
    if (lift_y1 - source_y1) % prime or (lift_y2 - source_y2) % prime:
        raise ArithmeticError("lifted points did not reduce to the source points")
    if discriminant_term != factor_plus * factor_minus:
        raise ArithmeticError("published discriminant factorization failed")
    if factor_plus - factor_minus != 4 * (
        t1 * pn + s1 * difference
    ):
        raise ArithmeticError("factor-difference identity failed")
    if t1 * (factor_plus - factor_minus) != 4 * lift_y1:
        raise ArithmeticError("factor difference did not bind the first ordinate")
    if lift_b == 0 or discriminant_term == 0:
        raise ValueError("singular lifted curve")

    factor_gcd = math.gcd(factor_plus, factor_minus)
    rank_one_support_obstructed = (
        abs(lift_b) > 1
        and factor_plus > 1
        and factor_minus > 1
        and factor_gcd == 1
    )

    return {
        "schema": SCHEMA,
        "source": {
            "prime": prime,
            "a": source_a % prime,
            "b": source_b % prime,
            "points": [[source_x1, source_y1], [source_x2, source_y2]],
        },
        "inputs": {
            "t1": t1,
            "t2": t2,
            "b1": b1,
            "b2": b2,
            "parameter_n": parameter_n,
        },
        "auxiliary": {
            "difference": difference,
            "gamma1": gamma1,
            "gamma2": gamma2,
            "delta1": delta1,
            "delta2": delta2,
            "s1": s1,
            "s2": s2,
        },
        "lift": {
            "a": lift_a,
            "b": lift_b,
            "points": [[lift_x1, lift_y1], [lift_x2, lift_y2]],
            "discriminant_term": discriminant_term,
            "factor_plus": factor_plus,
            "factor_minus": factor_minus,
            "factor_gcd": factor_gcd,
        },
        "boundary": {
            "factors_equal": factor_plus == factor_minus,
            "first_ordinate_zero": lift_y1 == 0,
            "coprime_factor_obstruction_to_published_rank_one_bound": (
                rank_one_support_obstructed
            ),
            "explanation": (
                "When abs(B), F+, and F- are nonunits and gcd(F+,F-)=1, "
                "the displayed descent bound has at least three prime supports "
                "and cannot certify rank at most one.  A rank-one certificate "
                "needs a unit exception, shared prime support, or a stronger descent."
            ),
        },
    }


def published_example(parameter_n: int) -> dict[str, Any]:
    return build_lift(
        prime=353,
        source_a=-1,
        source_b=16,
        t1=703,
        t2=439,
        b1=-21,
        b2=154,
        parameter_n=parameter_n,
    )
