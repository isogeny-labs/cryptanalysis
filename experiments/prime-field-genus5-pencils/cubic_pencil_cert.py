#!/usr/bin/env python3
"""Certify paired-cubic hyperelliptic transfers and their genus-five pencils."""

import argparse
from itertools import combinations, combinations_with_replacement, product
import json
import math
import random
import time

from sage.all import FunctionField, GF, HyperellipticCurve, PolynomialRing, matrix, vector


def paired_cubic(prime, genus, rng):
    field = GF(prime)
    ring = PolynomialRing(field, "x")
    x = ring.gen()
    numerator, denominator = x**3 + x, x**2 + 2
    fibers = {}
    for u in field:
        if denominator(u) == 0:
            continue
        t = numerator(u) / denominator(u)
        polynomial = numerator - t * denominator
        if polynomial.is_squarefree():
            fibers.setdefault(t, []).append(u)
    for _ in range(100):
        if len(fibers) < genus + 1:
            raise ValueError("There are too few ordinary rational fibers")
        ts = rng.sample(list(fibers), genus + 1)
        us = [rng.choice(fibers[t]) for t in ts]
        c = math.prod(denominator(u) for u in us) / field(2)**(genus + 1)
        f = c * math.prod((numerator - t * denominator) // (x - u) for t, u in zip(ts, us))
        assert f.degree() == 2 * genus + 2 and f.is_squarefree()
        return f, ts, us


def parity_cover(f, ts):
    field = f.base_ring()
    base = FunctionField(field, "t")
    t = base.gen()
    ring = PolynomialRing(base, "w")
    w = ring.gen()
    cubic = w**3 - t*w**2 + w - 2*t
    residues = ring(f) % cubic
    multiplication = matrix(base, 3, 3)
    for j in range(3):
        coordinates = (w**j * residues) % cubic
        multiplication.set_column(j, [coordinates[i] for i in range(3)])
    s1 = multiplication.trace()
    s2 = (s1**2 - (multiplication**2).trace()) / 2
    norm_root = f.leading_coefficient() * math.prod(t - a for a in ts)
    assert multiplication.det() == norm_root**2
    target_ring = PolynomialRing(base, "Z")
    z = target_ring.gen()
    equation = z**4 - 2*s1*z**2 - 8*norm_root*z + s1**2 - 4*s2
    return base.extension(equation, names="z"), equation, s1, norm_root


def canonical_quadrics(curve):
    base = curve.base_field()
    field = curve.constant_base_field()
    t = curve(base.gen())
    canonical = curve.different() - 2*t.divisor_of_poles()
    forms = canonical.basis_function_space()
    if len(forms) != 5:
        raise ValueError("This canonical-net check expects genus five")
    products = list(combinations_with_replacement(range(5), 2))
    expressions = [(forms[i]*forms[j]).list() for i, j in products]
    denominator = base.one().denominator()
    for expr in expressions:
        for coefficient in expr:
            denominator = denominator.lcm(coefficient.denominator())
    columns = [[(coefficient*denominator).numerator() for coefficient in expr]
               for expr in expressions]
    max_degree = max(piece.degree() for column in columns for piece in column)
    evaluations = matrix(field, [[column[j][d] for column in columns]
                                 for j in range(4) for d in range(max_degree + 1)])
    net = []
    for v in evaluations.right_kernel().basis():
        model = matrix(field, 5)
        for (i, j), value in zip(products, v):
            model[i, j] = model[j, i] = value if i == j else value/2
        net.append(model)
    return canonical, forms, net


def smooth_net(field, net):
    if len(net) != 3:
        return False, None
    ring = PolynomialRing(field, names=("U", "V", "W"))
    coords = ring.gens()
    disc = sum((a * matrix(ring, q) for a, q in zip(coords, net)), matrix(ring, 5)).det()
    if disc.degree() != 5:
        return False, disc
    chart = PolynomialRing(field, names=("a", "b"))
    for fixed in range(3):
        values = iter(chart.gens())
        mapping = ring.hom([chart.one() if i == fixed else next(values) for i in range(3)], chart)
        equations = [mapping(disc)] + [mapping(disc.derivative(t)) for t in coords]
        if chart.ideal(equations).groebner_basis() != [chart.one()]:
            return False, disc
    return True, disc


def simple_branch(function, canonical):
    poles = function.divisor_of_poles()
    if poles.degree() != 4:
        return None
    ramification = function.derivative().divisor() + canonical + 2*poles
    if ramification.degree() != 16:
        raise ArithmeticError("Incorrect ramification degree")
    values = set()
    for place, multiplicity in ramification.list():
        if multiplicity != 1:
            return None
        if function.valuation(place) < 0:
            if place.degree() != 1:
                return None
            key = ("infinity",)
        else:
            value = function.evaluate(place)
            polynomial = value.minpoly()
            if polynomial.degree() != place.degree():
                return None
            key = tuple(map(int, polynomial.list()))
        if key in values:
            return None
        values.add(key)
    return sorted(values, key=str)


def find_simple_pencil(field, canonical, forms, net, disc, rng):
    q = field.order()
    indices = [(1, a, b) for a in field for b in field] + [(0, 1, a) for a in field] + [(0, 0, 1)]
    rng.shuffle(indices)
    for coords in indices:
        if disc(*coords) != 0:
            continue
        equation = sum((a*Q for a, Q in zip(coords, net)), matrix(field, 5))
        if equation.rank() != 4:
            continue
        radical = equation.right_kernel().basis()[0]
        for _ in range(2):
            left = None
            for _ in range(8*q):
                u = vector(field, [rng.randrange(q) for _ in range(5)])
                if u.dot_product(equation*u) == 0 and matrix(field, [radical, u]).rank() == 2:
                    left = u
                    break
            if left is None:
                continue
            functional = (equation*left).row()
            hyperplane = functional.right_kernel().basis_matrix()
            for _ in range(8*q):
                coeffs = vector(field, [rng.randrange(q) for _ in range(4)])
                right = coeffs * hyperplane
                if right.dot_product(equation*right) != 0:
                    continue
                plane = matrix(field, [radical, left, right])
                if plane.rank() != 3:
                    continue
                a, b = plane.right_kernel().basis()
                function = sum(c*f for c, f in zip(a, forms)) / sum(c*f for c, f in zip(b, forms))
                branches = simple_branch(function, canonical)
                if branches is not None:
                    return list(map(int, coords)), branches, [list(map(int, a)), list(map(int, b))]
                break
    return None


def sample_curve(prime, seed, attempts, find_pencil):
    rng = random.Random(seed)
    start = time.perf_counter()
    for _ in range(attempts):
        f, ts, us = paired_cubic(prime, 5, rng)
        X, quartic, _, _ = parity_cover(f, ts)
        if X.genus() != 5:
            raise ArithmeticError("Genus mismatch")
        canonical, forms, net = canonical_quadrics(X)
        smooth, disc = smooth_net(f.base_ring(), net)
        record = {
            "q": prime, "omitted_roots": list(map(int, us)), "branch_values": list(map(int, ts)),
            "source_polynomial": list(map(int, f.list())), "canon_quadric_count": len(net),
            "smooth_discriminant": smooth, "seconds": time.perf_counter()-start,
        }
        if not smooth:
            print(json.dumps(record), flush=True)
            continue
        # A smooth discriminant rules out net rank <=3. The canonical quadrics
        # must still have a one-dimensional projective base locus for this test.
        field = f.base_ring()
        ring = PolynomialRing(field, 5, "X")
        variables = vector(ring, ring.gens())
        eqs = [variables.dot_product(matrix(ring, Q)*variables) for Q in net]
        dimension = ring.ideal(eqs).dimension()
        record["canonical_cone_dimension"] = dimension
        if dimension == 2 and find_pencil:
            result = find_simple_pencil(field, canonical, forms, net, disc, rng)
            if result is not None:
                record["net_coordinates"], record["branch_polynomial_factors"], record["ruling_forms"] = result
        record["seconds"] = time.perf_counter()-start
        print(json.dumps(record), flush=True)
        if "ruling_forms" in record:
            return


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("primes", type=int, nargs="+")
    parser.add_argument("--seed", type=int, default=44)
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--find-pencil", action="store_true")
    args = parser.parse_args()
    for q in args.primes:
        if q <= 5 or q == 17 or not GF(q).is_prime_field():
            parser.error("supply prime fields of characteristic greater than five, excluding 17")
        sample_curve(q, args.seed, args.attempts, args.find_pencil)


if __name__ == "__main__":
    main()
