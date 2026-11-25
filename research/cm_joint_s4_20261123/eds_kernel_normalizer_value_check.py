#!/usr/bin/env sage -python
"""Exact value checks for K(x(P)) = 2*y(P)*Phi(P)^r."""

from sage.all import EllipticCurve, GF, PolynomialRing, ZZ


def check(name, curve, generator, labels):
    p = int(curve.base_field().cardinality())
    r = int(curve.cardinality())
    assert int(generator.order()) == r and r >= 5 and r % 2
    exponent = pow(r*r, -1, p-1)
    field = curve.base_field()
    ring = PolynomialRing(field, "X")
    X = ring.gen()
    a, b = curve.a4(), curve.a6()
    kernel = ring.prod(X-field(x) for x in range(p)
        if pow(int(field(x)**3+a*field(x)+b), (p-1)//2, p) == p-1)

    def w(point, n):
        return curve.division_polynomial(
            ZZ(n), (point[0], point[1]),
            two_torsion_multiplicity=1, force_evaluate=0)

    chi2 = 1 if field(2)**((p-1)//2) == 1 else -1
    for d in labels:
        point = d*generator
        numerator = w(point, p-1)
        denominator = w(point, p-1+r)
        assert numerator and denominator
        phi = (numerator/denominator)**exponent
        assert kernel(point[0]) == field(2)*point[1]*phi**r
        kernel_sign = 1 if kernel(point[0])**((p-1)//2) == 1 else -1
        normalized_sign = 1 if (point[1]*phi)**((p-1)//2) == 1 else -1
        assert kernel_sign == chi2*normalized_sign
    print(name, r, len(labels), "exact values", "chi2", chi2)


def main():
    f47 = GF(47)
    e19 = EllipticCurve(f47, [1, 38])
    e163 = EllipticCurve(f47, [5, 8])
    check("D-19", e19, e19(2, 1), range(1, 61))
    check("D-163", e163, e163(19, 37), range(1, 53))

    f1009 = GF(1009)
    source = EllipticCurve(f1009, [4, 10])
    edge = source.isogenies_prime_degree(5)[0]
    generator = source.gens()[0]
    labels = (1, 2, 3, 5, 7, 11, 13, 17)
    check("source-1009", source, generator, labels)
    check("endpoint-1009", edge.codomain(), edge(generator), labels)

    f43 = GF(43)
    opposite = EllipticCurve(f43, [1, 3])
    assert int(opposite.cardinality()) == 47
    check("chi2-negative", opposite, opposite.gens()[0], range(1, 47))


if __name__ == "__main__":
    main()
