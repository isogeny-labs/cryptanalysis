#!/usr/bin/env python3
"""Verify a Frey–Rück transfer for a small rational genus-two subgroup."""
from random import Random

from sage.all import GF, HyperellipticCurve, Matrix, PolynomialRing, vector


def torsion_function(divisor, order, curve_polynomial):
    """Return A and B for a function A(x)+B(x)y with divisor order*D."""
    u, v = divisor[0], divisor[1]
    ring = u.parent()
    field = ring.base_ring()
    x = ring.gen()
    degree = int(u.degree())
    if degree <= 0 or u.gcd(2 * v) != 1:
        raise ValueError("expected a nonzero unramified Mumford divisor")

    inverse = (2 * v).inverse_mod(u)
    lift = v
    modulus = u
    for _ in range(1, order):
        error, remainder = (curve_polynomial - lift**2).quo_rem(modulus)
        assert remainder == 0
        lift += modulus * (error * inverse % u)
        modulus *= u
    assert (curve_polynomial - lift**2) % modulus == 0

    # At the unique infinity, x and y have pole orders 2 and 5.
    pole_order = order * degree
    a_powers = [x**index for index in range(pole_order // 2 + 1)]
    b_powers = [x**index for index in range((pole_order - 5) // 2 + 1)]
    residues = [term % modulus for term in a_powers]
    residues.extend(term * lift % modulus for term in b_powers)
    kernel = Matrix(
        field,
        [[entry[index] for entry in residues] for index in range(pole_order)],
    ).right_kernel()
    assert kernel.dimension() == 1
    coefficients = kernel.basis()[0]
    split = len(a_powers)
    a = sum((coeff * term for coeff, term in zip(coefficients[:split], a_powers)), ring.zero())
    b = sum((coeff * term for coeff, term in zip(coefficients[split:], b_powers)), ring.zero())
    norm = a**2 - curve_polynomial * b**2
    assert norm.degree() == pole_order
    assert norm == norm.leading_coefficient() * modulus
    assert (a + b * lift) % modulus == 0
    return a, b


def evaluate(function, point):
    a, b = function
    x, y = point
    return a(x) + b(x) * y


def tiny_field_logs(field, order):
    """Build factor-base logs modulo order and return individual descent."""
    primitive = field.multiplicative_generator()
    scalars = GF(order)
    base = (2, 3, 5)

    def smooth_lift(value):
        remaining = int(value)
        exponents = []
        for prime in base:
            count = 0
            while remaining % prime == 0:
                remaining //= prime
                count += 1
            exponents.append(count)
        return exponents if remaining == 1 else None

    rows = []
    powers = []
    for exponent in range(1, field.order()):
        row = smooth_lift(primitive**exponent)
        if row is None:
            continue
        rows.append(row)
        powers.append(exponent)
        if Matrix(scalars, rows).rank() == len(base):
            break
    logs = Matrix(scalars, rows).solve_right(vector(scalars, powers))
    assert all(primitive**(int(logs[index]) * ((field.order() - 1) // order))
               == field(prime)**((field.order() - 1) // order)
               for index, prime in enumerate(base))

    def descend(value):
        for exponent in range(field.order() - 1):
            smooth = smooth_lift(value * primitive**exponent)
            if smooth is not None:
                return vector(scalars, smooth).dot_product(logs) - exponent
        raise AssertionError("no smooth field lift found")

    return primitive, base, tuple(map(int, logs)), descend


def main():
    p, r = 29, 7
    field = GF(p)
    ring = PolynomialRing(field, "x")
    x = ring.gen()
    f = x**5 + 16*x**4 + 20*x**3 + 14*x**2 + 12*x + 4
    curve = HyperellipticCurve(f)
    jacobian = curve.jacobian()
    group = jacobian(field)
    order = int(jacobian.cardinality())
    assert order == 896 and order % r == 0
    points = sorted(
        ((point[0], point[1]) for point in curve.rational_points() if point[2] == 1),
        key=lambda point: (int(point[0]), int(point[1])),
    )
    for p0, p1 in points:
        divisor = (order // r) * group((x - p0, ring(p1)))
        if divisor and all((multiple * divisor)[0].gcd(2 * (multiple * divisor)[1]) == 1
                           for multiple in range(1, r)):
            break
    else:
        raise AssertionError("no unramified subgroup generator found")
    assert not r * divisor

    functions = {multiple: torsion_function(multiple * divisor, r, f)
                 for multiple in range(1, r)}
    exponent = (p - 1) // r
    usable = [point for point in points
              if all(evaluate(function, point) for function in functions.values())]
    for point in usable:
        for other in usable:
            pairing = (evaluate(functions[1], point) / evaluate(functions[1], other))**exponent
            if pairing != 1:
                break
        else:
            continue
        break
    else:
        raise AssertionError("no nontrivial rational pairing evaluation")
    assert pairing**r == 1

    for multiple, function in functions.items():
        value = (evaluate(function, point) / evaluate(function, other))**exponent
        assert value == pairing**multiple
    seed = 92517
    secret = Random(seed).randrange(2, r)
    target = secret * divisor
    a, b = torsion_function(target, r, f)
    target_pairing = ((evaluate((a, b), point) / evaluate((a, b), other))**exponent)
    primitive, factor_base, field_logs, descend = tiny_field_logs(field, r)
    recovered = int(descend(target_pairing) / descend(pairing))
    assert recovered == secret and recovered * divisor == target

    print("Curve:", curve)
    print("Point counts over F_29 and F_29^2:", curve.count_points(2))
    print("Jacobian order:", order, "subgroup order:", r)
    print("Cofactor source point:", (p0, p1))
    print("Generator Mumford (u, v):", (divisor[0], divisor[1]))
    print("Evaluation divisor E = P - Q:", point, "-", other)
    print("Generator A, B:", functions[1])
    print("Generator reduced Tate pairing:", pairing)
    print("Verified bilinearity on all six nonzero generator multiples")
    print("Target Mumford (u, v):", (target[0], target[1]))
    print("Target reduced Tate pairing:", target_pairing)
    print("Field primitive root:", primitive)
    print("Field factor base:", factor_base, "logs modulo 7:", field_logs)
    print("Seed:", seed, "known exponent:", secret, "recovered exponent:", recovered)
    print("Verified recovered exponent in the Jacobian")


if __name__ == "__main__":
    main()
