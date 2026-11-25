#!/usr/bin/env sage -python
"""Direct finite value checks for the generic anti-Frobenius kernel identity."""

from sage.all import EllipticCurve, GF, PolynomialRing, ZZ


def check(name, curve, generator, labels):
    p = int(curve.base_field().cardinality())
    r = int(curve.cardinality())
    assert int(generator.order()) == r and r % 2 == 1
    h = (r-1)//2
    field = curve.base_field()
    ring = PolynomialRing(field, "X")
    X = ring.gen()
    a, b = curve.a4(), curve.a6()
    kernel = ring.prod(X-field(x) for x in range(p)
        if pow(int(field(x)**3+a*field(x)+b), (p-1)//2, p) == p-1)
    assert int(kernel.degree()) == (2*(p+1)-r-1)//2
    for d in labels:
        point = d*generator
        def w(n):
            return curve.division_polynomial(
                ZZ(n), (point[0], point[1]),
                two_torsion_multiplicity=1, force_evaluate=0)
        assert w(2)*w(h)*w(h+1) != 0
        assert kernel(point[0]) == -w(2)*w(h)/w(h+1)
    print(name, r, len(labels), "exact values")


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


if __name__ == "__main__":
    main()
