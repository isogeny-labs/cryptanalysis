#!/usr/bin/env python3
"""Verify the nonsplit genus-five paired-cubic example and its pencil locus."""

from itertools import combinations
import json
import math

from sage.all import GF, HyperellipticCurve, PolynomialRing, euler_phi, matrix, vector

from cubic_pencil_cert import canonical_quadrics, parity_cover, simple_branch


PRIME = 19
OMITTED_ROOTS = (18, 8, 10, 14, 5, 16)
SOURCE_COEFFICIENTS = (15, 14, 1, 11, 1, 5, 1, 4, 5, 0, 16, 5, 8)
WEIL_COEFFICIENTS = (2476099, -781926, 240065, 8664, -9766, 4988, -514, 24, 35, -6, 1)
RULING_FORMS = ((1, 0, 1, 16, 0), (0, 1, 13, 16, 17))
BRANCH_FACTORS = ((12, 16, 11, 5, 2, 7, 2, 1), (17, 5, 3, 7, 13, 2, 8, 0, 18, 1))


def source_curve(field):
    ring = PolynomialRing(field, "x")
    x = ring.gen()
    numerator, denominator = x**3 + x, x**2 + 2
    derivative = numerator.derivative()*denominator - numerator*denominator.derivative()
    assert derivative.degree() == 4 and derivative.is_squarefree()
    assert derivative.gcd(denominator).degree() == 0
    roots = [field(u) for u in OMITTED_ROOTS]
    values = [numerator(u) / denominator(u) for u in roots]
    assert tuple(map(int, values)) == (12, 5, 14, 17, 2, 18)
    fibers = [numerator - value*denominator for value in values]
    assert all(fiber.is_squarefree() for fiber in fibers)
    quadratics = [fiber // (x - omitted) for fiber, omitted in zip(fibers, roots)]
    scale = math.prod(denominator(u) for u in roots) / field(2)**len(roots)
    polynomial = scale*math.prod(quadratics)
    assert tuple(map(int, polynomial.list())) == SOURCE_COEFFICIENTS
    assert polynomial.is_squarefree()
    return polynomial, values, numerator, denominator, quadratics


def verify_recognition(polynomial, numerator, denominator, quadratics):
    extension = polynomial.splitting_field("b")
    positions = list(combinations(range(4), 2))
    rows = []
    for quadratic in quadratics:
        x, y = quadratic.change_ring(extension).roots(multiplicities=False)
        rows.append([x**i*y**j - x**j*y**i for i, j in positions])
    expected = [
        numerator[i]*denominator[j] - numerator[j]*denominator[i]
        for i, j in positions
    ]
    for five in combinations(rows, 5):
        equations = matrix(extension, five)
        assert equations.rank() == 5
        assert not any(equations*vector(extension, expected))
    return len(list(combinations(rows, 5)))


def verify_net(field, net):
    assert len(net) == 3
    ring = PolynomialRing(field, names=("U", "V", "W"))
    u, v, w = ring.gens()
    determinant = sum((t*matrix(ring, q) for t, q in zip((u, v, w), net)), matrix(ring, 5)).det()
    factors = list(determinant.factor())
    assert len(factors) == 1 and factors[0][0].degree() == 5 and factors[0][1] == 1
    smooth_point = (1, 0, 14)
    node = (1, 11, 16)
    assert determinant(*smooth_point) == 0
    assert any(derivative(*smooth_point) != 0 for derivative in determinant.gradient())
    assert determinant(*node) == 0
    assert all(derivative(*node) == 0 for derivative in determinant.gradient())
    node_quadric = sum((a*q for a, q in zip(node, net)), matrix(field, 5))
    assert node_quadric.rank() == 3
    hessian = matrix(field, [[determinant.derivative(a).derivative(b)(*node) for b in (v, w)] for a in (v, w)])
    assert hessian.det() == 11
    chart = PolynomialRing(field, names=("V", "W"))
    cv, cw = chart.gens()
    to_chart = ring.hom([chart.one(), cv, cw], chart)
    singular_ideal = chart.ideal([to_chart(determinant)] + [to_chart(d) for d in determinant.gradient()])
    assert singular_ideal.groebner_basis() == [cv + 8, cw + 3]
    canonical = PolynomialRing(field, 5, "X")
    coords = vector(canonical, canonical.gens())
    equations = [coords.dot_product(matrix(canonical, quadric)*coords) for quadric in net]
    cone_dimension = canonical.ideal(equations).dimension()
    assert cone_dimension == 2
    return determinant, smooth_point, node, cone_dimension


def verify_pencil(field, canonical, forms, net):
    numerator, denominator = (vector(field, coefficients) for coefficients in RULING_FORMS)
    quadric_point = (1, 7, 17)
    quadric = sum((a*q for a, q in zip(quadric_point, net)), matrix(field, 5))
    assert quadric.rank() == 4
    plane = matrix(field, [numerator, denominator]).right_kernel().basis_matrix()
    assert plane.nrows() == 3
    assert (plane*quadric*plane.transpose()).is_zero()
    function = sum(a*form for a, form in zip(numerator, forms)) / sum(b*form for b, form in zip(denominator, forms))
    branch_factors = simple_branch(function, canonical)
    assert branch_factors is not None and set(branch_factors) == set(BRANCH_FACTORS)
    return quadric_point, branch_factors


def verify_absolute_simplicity(weil):
    reduced = weil.change_ring(GF(31))
    assert reduced.is_irreducible()
    field = GF(31**10, "a", modulus=reduced)
    root = field.gen()
    orders = [order for order in range(2, 16201) if euler_phi(order) <= 90]
    for order in orders:
        assert all(root**(order*(31**degree - 1)) != 1 for degree in (1, 2, 5))
    return len(orders)


def main():
    field = GF(PRIME)
    polynomial, values, numerator, denominator, quadratics = source_curve(field)
    rank_checks = verify_recognition(polynomial, numerator, denominator, quadratics)
    weil = HyperellipticCurve(polynomial).frobenius_polynomial()
    assert tuple(map(int, weil.list())) == WEIL_COEFFICIENTS
    orders_checked = verify_absolute_simplicity(weil)

    target, _, _, _ = parity_cover(polynomial, values)
    assert target.genus() == 5
    canonical, forms, net = canonical_quadrics(target)
    determinant, smooth_point, node, cone_dimension = verify_net(field, net)
    pencil_point, branch_factors = verify_pencil(field, canonical, forms, net)
    print(json.dumps({
        "q": PRIME,
        "source_polynomial": SOURCE_COEFFICIENTS,
        "omitted_roots": OMITTED_ROOTS,
        "paired_values": list(map(int, values)),
        "rank_five_subsets_verified": rank_checks,
        "weil_polynomial": WEIL_COEFFICIENTS,
        "weil_polynomial_irreducible_mod": 31,
        "root_of_unity_orders_excluded": orders_checked,
        "target_genus": 5,
        "canonical_cone_dimension": int(cone_dimension),
        "determinant_quintic": str(determinant),
        "rational_smooth_point": smooth_point,
        "ordinary_rank_three_node": node,
        "node_hessian_determinant": 11,
        "simply_branched_pencil_net_point": pencil_point,
        "ruling_forms": RULING_FORMS,
        "branch_factors": branch_factors,
    }, indent=2))


if __name__ == "__main__":
    main()
