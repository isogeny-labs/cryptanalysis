#!/usr/bin/env sage -python
"""Exact principal-unit arithmetic at (pi-1)^2 on two public curves."""

from sage.all import QuadraticField, ZZ


INSTANCES = (
    ("D-19", ZZ(47), ZZ(61)),
    ("P-192", ZZ(6277101735386680763835789423207666416083908700390324961279),
     ZZ(6277101735386680763835789423176059013767194773182842284081)),
)


def main():
    for name, p, r in INSTANCES:
        t = p + 1 - r
        disc = t*t - 4*p
        assert disc.is_fundamental_discriminant() and r.is_prime()
        assert disc.gcd(r) == 1 and r != p
        K = QuadraticField(disc, "s")
        pi = (t + K.gen())/2
        eta = pi - 1
        n = K.ideal(eta)
        n2 = n*n
        assert n.norm() == r and n2.norm() == r*r
        assert eta not in n2 and r*eta in n2
        # Local principal-unit addition and an explicit smooth-ideal residue.
        assert (1 + 3*eta)*(1 + 5*eta) - (1 + 8*eta) in n2
        assert (1 + pi)/2 - (1 + eta/2) in n2
        assert (1 + eta/2) - 1 not in n2
        if name == "D-19":
            assert K.class_number() == 1
            for a in range(int(r)):
                for b in range(int(r)):
                    assert ((1+a*eta)*(1+b*eta)-(1+(a+b)*eta)) in n2
                    assert (((1+a*eta)-(1+b*eta)) in n2) == (a == b)
            assert all((pi**k-1 in n2) == (k % r == 0)
                       for k in range(2*int(r)+1))
            assert (1 + pi).norm() == 35
        print(f"{name}: norm(n)={r}, norm(n^2)={r*r}, principal-unit order={r}")


if __name__ == "__main__":
    main()
