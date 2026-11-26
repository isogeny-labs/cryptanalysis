#!/usr/bin/env python3
"""Measure static certificate degree for planted binary Graeffe inversion."""

from math import comb
import json
from pathlib import Path
from random import Random

from sympy import Integer, Poly, symbols

from multisection_span_control import section_basis
from toy_jacobian import PrimePolynomials


FIXTURE = Path(__file__).with_name("multisection_span_control.json")
SEED = 442


def monomials(variables, bound):
    out = []

    def visit(index, left, prefix):
        if index == variables - 1:
            for value in range(left + 1):
                out.append(tuple(prefix + [value]))
            return
        for value in range(left + 1):
            visit(index + 1, left - value, prefix + [value])

    visit(0, bound, [])
    return sorted(set(out), key=lambda exponent: (sum(exponent), exponent))


def graeffe_system(poly, curve, genus, r, rng):
    u, v, f = curve
    q = genus + r
    basis = section_basis(poly, u, v, r)
    fixed = (r - 1) // 2 if r % 2 else r
    variables = symbols(f"z0:{r}")
    parameters = []
    cursor = 0
    for index in range(r + 1):
        if index == fixed:
            parameters.append(Integer(1))
        else:
            parameters.append(variables[cursor])
            cursor += 1

    coefficients = [Integer(0)] * (q + 1)
    for i, (bi, ai) in enumerate(basis):
        for j, (bj, aj) in enumerate(basis):
            numerator = poly.sub(
                poly.mul(poly.mul(bi, bj), f),
                poly.mul(ai, aj),
            )
            quotient = poly.exact_quotient(numerator, u)
            for degree, value in enumerate(quotient):
                coefficients[degree] += parameters[i] * parameters[j] * value
    leading = int(coefficients[q]) % poly.p
    assert leading in (1, poly.p - 1)
    if leading == poly.p - 1:
        coefficients = [-value for value in coefficients]

    even = coefficients[::2]
    odd = coefficients[1::2]
    transformed = [Integer(0)] * (q + 1)
    sign = 1 if q % 2 == 0 else -1
    for i, left in enumerate(even):
        for j, right in enumerate(even):
            transformed[i + j] += sign * left * right
    for i, left in enumerate(odd):
        for j, right in enumerate(odd):
            transformed[i + j + 1] -= sign * left * right

    planted = [rng.randrange(poly.p) for _ in range(r)]
    substitution = dict(zip(variables, planted, strict=True))
    equations = []
    for coefficient in transformed[:-1]:
        value = int(coefficient.subs(substitution)) % poly.p
        equations.append(Poly(coefficient - value, *variables, modulus=poly.p))
    return variables, planted, equations


def polynomial_dict(polynomial, prime):
    return {
        tuple(monomial): int(coefficient) % prime
        for monomial, coefficient in polynomial.terms()
        if int(coefficient) % prime
    }


def add_echelon_row(pivots, row, prime):
    while row:
        leading = max(row, key=lambda exponent: (sum(exponent), exponent))
        coefficient = row[leading] % prime
        if leading not in pivots:
            inverse = pow(coefficient, -1, prime)
            pivots[leading] = {
                monomial: value * inverse % prime
                for monomial, value in row.items()
                if value % prime
            }
            return
        pivot = pivots[leading]
        for monomial, value in pivot.items():
            new_value = (row.get(monomial, 0) - coefficient * value) % prime
            if new_value:
                row[monomial] = new_value
            elif monomial in row:
                del row[monomial]


def reduces_to_zero(pivots, row, prime):
    while row:
        leading = max(row, key=lambda exponent: (sum(exponent), exponent))
        coefficient = row[leading] % prime
        if leading not in pivots:
            return False
        for monomial, value in pivots[leading].items():
            new_value = (row.get(monomial, 0) - coefficient * value) % prime
            if new_value:
                row[monomial] = new_value
            elif monomial in row:
                del row[monomial]
    return True


def certificate_panel(equations, planted, variables, prime, limit=12):
    count = len(variables)
    inputs = [
        (polynomial_dict(equation, prime), equation.total_degree())
        for equation in equations
    ]
    for degree in range(1, limit + 1):
        pivots = {}
        for coefficients, input_degree in inputs:
            if input_degree > degree:
                continue
            for multiplier in monomials(count, degree - input_degree):
                row = {
                    tuple(x + y for x, y in zip(monomial, multiplier, strict=True)):
                    coefficient
                    for monomial, coefficient in coefficients.items()
                }
                add_echelon_row(pivots, row, prime)

        recovered = []
        for index in range(count):
            exponent = [0] * count
            exponent[index] = 1
            target = {tuple(exponent): 1}
            constant = -planted[index] % prime
            if constant:
                target[(0,) * count] = constant
            recovered.append(reduces_to_zero(pivots, target, prime))
        if all(recovered):
            columns = comb(count + degree, count)
            return {
                "minimum_static_certificate_degree": degree,
                "macaulay_columns_at_certificate": columns,
                "macaulay_rank_at_certificate": len(pivots),
                "quotient_dimension_at_certificate": columns - len(pivots),
                "all_parameter_linear_forms_recovered": True,
            }
    raise AssertionError("certificate limit too small")


def main():
    fixture = json.loads(FIXTURE.read_text())
    prime = fixture["prime"]
    genus = 2
    data = fixture["curves"][str(genus)]
    curve = (tuple(data["u"]), tuple(data["v"]), tuple(data["f"]))
    poly = PrimePolynomials(prime)
    rng = Random(SEED)
    panels = []
    for r in range(1, 5):
        variables, planted, equations = graeffe_system(
            poly, curve, genus, r, rng
        )
        item = {
            "projective_section_dimension": r,
            "tail_slots": genus + r,
            "variables": r,
            "equations": len(equations),
            "input_degrees": [equation.total_degree() for equation in equations],
            "planted_parameters": planted,
        }
        item.update(certificate_panel(equations, planted, variables, prime))
        panels.append(item)
    result = {
        "prime": prime,
        "genus": genus,
        "subgroup_order": 2,
        "seed": SEED,
        "panels": panels,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
