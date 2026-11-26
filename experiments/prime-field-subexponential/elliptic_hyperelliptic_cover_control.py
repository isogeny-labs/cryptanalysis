#!/usr/bin/env python3
"""Construct hyperelliptic genus-2--7 covers of one elliptic curve."""

from collections import Counter
import json

from sympy import Poly, symbols


PRIME = 101
ELLIPTIC_MODELS = ((2, 3), (0, 1), (1, 0), (5, 7), (13, 29), (47, 11))
T = symbols("t")


def poly(expression):
    return Poly(expression, T, modulus=PRIME)


def value(polynomial, argument):
    return int(polynomial.eval(argument)) % PRIME


def coefficients(polynomial):
    return [int(coefficient) % PRIME for coefficient in polynomial.all_coeffs()]


def roots(square):
    return [value for value in range(PRIME) if value * value % PRIME == square]


def elliptic_rhs(x, a_coefficient, b_coefficient):
    return (x**3 + a_coefficient * x + b_coefficient) % PRIME


def parameters(genus):
    degree = (genus + 2) // 2
    odd_poles = 2 * genus + 2 - 3 * degree
    assert 0 <= odd_poles <= degree
    assert (odd_poles - degree) % 2 == 0
    return degree, odd_poles


def denominator(degree, odd_poles):
    """Return D=S^2 K with exactly odd_poles odd-multiplicity roots."""
    if odd_poles == 0:
        assert degree % 2 == 0
        return poly(1), poly(1), poly(1)
    first_multiplicity = degree - odd_poles + 1
    assert first_multiplicity % 2 == 1
    d_expression = T**first_multiplicity
    s_expression = T**((first_multiplicity - 1) // 2)
    k_expression = T
    for root in range(1, odd_poles):
        d_expression *= T - root
        k_expression *= T - root
    d_polynomial = poly(d_expression)
    s_polynomial = poly(s_expression)
    k_polynomial = poly(k_expression)
    assert d_polynomial == s_polynomial * s_polynomial * k_polynomial
    assert d_polynomial.degree() == degree
    assert k_polynomial.degree() == odd_poles
    return d_polynomial, s_polynomial, k_polynomial


def construct(genus, a_coefficient, b_coefficient):
    degree, odd_poles = parameters(genus)
    d_polynomial, s_polynomial, k_polynomial = denominator(
        degree, odd_poles
    )
    for shift in range(PRIME):
        if odd_poles == 0:
            n_polynomial = poly(T**degree + shift)
        else:
            n_polynomial = poly(1 + shift * d_polynomial.as_expr())
        g_polynomial = poly(
            n_polynomial.as_expr() ** 3
            + a_coefficient
            * n_polynomial.as_expr()
            * d_polynomial.as_expr() ** 2
            + b_coefficient * d_polynomial.as_expr() ** 3
        )
        if g_polynomial.degree() != 3 * degree:
            continue
        if g_polynomial.gcd(g_polynomial.diff()).degree() != 0:
            continue
        if g_polynomial.gcd(d_polynomial).degree() != 0:
            continue
        h_polynomial = g_polynomial * k_polynomial
        if h_polynomial.gcd(h_polynomial.diff()).degree() != 0:
            continue
        break
    else:
        raise AssertionError("no good shift")

    assert h_polynomial.degree() == 2 * genus + 2
    assert poly(
        d_polynomial.as_expr() * g_polynomial.as_expr()
        - s_polynomial.as_expr() ** 2 * h_polynomial.as_expr()
    ).is_zero

    mapped_fibers = Counter()
    affine_curve_points = 0
    pole_points = 0
    for t_value in range(PRIME):
        d_value = value(d_polynomial, t_value)
        for z_value in roots(value(h_polynomial, t_value)):
            affine_curve_points += 1
            if d_value == 0:
                assert z_value == 0
                pole_points += 1
                continue
            n_value = value(n_polynomial, t_value)
            s_value = value(s_polynomial, t_value)
            inverse_d = pow(d_value, -1, PRIME)
            x_value = n_value * inverse_d % PRIME
            y_value = (
                z_value * s_value * pow(d_value, -2, PRIME)
            ) % PRIME
            assert y_value * y_value % PRIME == elliptic_rhs(
                x_value, a_coefficient, b_coefficient
            )
            mapped_fibers[(x_value, y_value)] += 1

    elliptic_affine_points = sum(
        len(roots(elliptic_rhs(x_value, a_coefficient, b_coefficient)))
        for x_value in range(PRIME)
    )
    histogram = Counter(mapped_fibers.values())
    return {
        "genus": genus,
        "cover_degree": degree,
        "odd_poles": odd_poles,
        "shift": shift,
        "numerator": coefficients(n_polynomial),
        "denominator": coefficients(d_polynomial),
        "square_part": coefficients(s_polynomial),
        "odd_pole_kernel": coefficients(k_polynomial),
        "hyperelliptic_polynomial": coefficients(h_polynomial),
        "hyperelliptic_degree": h_polynomial.degree(),
        "branch_points": 3 * degree + odd_poles,
        "affine_curve_points": affine_curve_points,
        "affine_pole_points_mapping_to_elliptic_infinity": pole_points,
        "mapped_finite_elliptic_points": len(mapped_fibers),
        "finite_fiber_size_histogram": {
            str(size): count for size, count in sorted(histogram.items())
        },
        "elliptic_affine_points": elliptic_affine_points,
        "map_identity_verified_on_every_affine_nonpole_point": True,
        "squarefree_hyperelliptic_model": True,
    }


def main():
    models = []
    for a_coefficient, b_coefficient in ELLIPTIC_MODELS:
        discriminant = (
            -16 * (4 * a_coefficient**3 + 27 * b_coefficient**2)
        ) % PRIME
        assert discriminant
        models.append({
            "elliptic_curve": {
                "A": a_coefficient,
                "B": b_coefficient,
                "discriminant": discriminant,
            },
            "covers": [
                construct(genus, a_coefficient, b_coefficient)
                for genus in range(2, 8)
            ],
        })
    result = {
        "prime": PRIME,
        "models": models,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
