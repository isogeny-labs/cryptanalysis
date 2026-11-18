#!/usr/bin/env python3
"""L3 gate: exact count of P1 + P2 + P3 = T0 relations over a polynomial-span
factor base on binary curves, compared with the heuristic estimate.

Curve  E: y^2 + x y = x^3 + a x^2 + b  over GF(2^n) = GF(2)[z]/(f), n odd.
T0 = (0, sqrt b) is the 2-torsion point; -T0 = T0.
Factor base: points with x in V = {polynomials in z of degree < l}, x != 0.

For every ordered pair (P1, P2) of factor-base points, P3 = T0 - (P1 + P2) is
determined, and x(P3) = sqrt(b) / x(P1 + P2) (translation by T0 maps
x -> sqrt(b)/x). The pair is a relation iff that x lies in V \\ {0}.
The script checks this identity against a full group addition on a sample
of pairs before counting.

Reported per (n, l, seed): N = number of factor-base points, ordered point
triples, unordered x-sets, and the estimates
  ordered  ~ N^3 / 2^n
  x-sets   ~ N^3 / (12 * 2^n)   (3! orderings, 2 global sign patterns)
together with 2^(3l-n)/6, the figure quoted in the leads note.

Pure Python, deterministic seeds, standard library only.
"""
import json
import random
import sys


def deg(p):
    return p.bit_length() - 1


def pmod(p, f):
    df = deg(f)
    while p and deg(p) >= df:
        p ^= f << (deg(p) - df)
    return p


def pmul(a, b, f):
    r = 0
    while b:
        if b & 1:
            r ^= a
        b >>= 1
        a <<= 1
        if a >> deg(f) & 1:
            a ^= f
    return r


def pgcd(a, b):
    while b:
        a, b = b, pmod(a, b)
    return a


def ppowx2k(k, f):
    """x^(2^k) mod f."""
    r = 2
    for _ in range(k):
        r = pmul(r, r, f)
    return r


def irreducible(f):
    n = deg(f)
    if ppowx2k(n, f) != 2:
        return False
    for q in {q for q in range(2, n + 1) if n % q == 0 and all(q % r for r in range(2, q))}:
        if pgcd(f, ppowx2k(n // q, f) ^ 2) != 1:
            return False
    return True


def find_modulus(n):
    for k in range(1, n):  # trinomials first
        f = (1 << n) | (1 << k) | 1
        if irreducible(f):
            return f
    for k3 in range(3, n):
        for k2 in range(2, k3):
            for k1 in range(1, k2):
                f = (1 << n) | (1 << k3) | (1 << k2) | (1 << k1) | 1
                if irreducible(f):
                    return f
    raise ValueError(n)


class Field:
    def __init__(self, n):
        self.n = n
        self.f = find_modulus(n)

    def mul(self, a, b):
        return pmul(a, b, self.f)

    def sq(self, a):
        return pmul(a, a, self.f)

    def inv(self, a):
        # extended Euclid in GF(2)[z]
        u, v, g1, g2 = a, self.f, 1, 0
        while u != 1:
            j = deg(u) - deg(v)
            if j < 0:
                u, v, g1, g2 = v, u, g2, g1
                j = -j
            u ^= v << j
            g1 ^= g2 << j
        return pmod(g1, self.f)

    def trace(self, a):
        t, s = 0, a
        for _ in range(self.n):
            t ^= s
            s = self.sq(s)
        return t

    def halftrace(self, a):  # n odd
        h, s = 0, a
        for i in range((self.n - 1) // 2 + 1):
            h ^= s
            s = self.sq(self.sq(s))
        return h

    def sqrt(self, a):
        for _ in range(self.n - 1):
            a = self.sq(a)
        return a


class Curve:
    def __init__(self, F, a, b):
        self.F, self.a, self.b = F, a, b
        self.sb = F.sqrt(b)

    def on(self, P):
        x, y = P
        F = self.F
        return F.sq(y) ^ F.mul(x, y) == F.mul(F.sq(x), x) ^ F.mul(self.a, F.sq(x)) ^ self.b

    def lift(self, x):
        """Points with abscissa x != 0, or []."""
        F = self.F
        c = x ^ self.a ^ F.mul(self.b, F.inv(F.sq(x)))
        if F.trace(c):
            return []
        w = F.halftrace(c)
        y = F.mul(x, w)
        return [(x, y), (x, y ^ x)]

    def add(self, P, Q):
        """Affine addition; None is the point at infinity."""
        F = self.F
        if P is None:
            return Q
        if Q is None:
            return P
        (x1, y1), (x2, y2) = P, Q
        if x1 == x2:
            if y1 ^ y2 == x1 or x1 == 0:  # Q = -P (covers T0 + T0)
                return None
            lam = x1 ^ F.mul(y1, F.inv(x1))
            x3 = F.sq(lam) ^ lam ^ self.a
            y3 = F.sq(x1) ^ F.mul(lam ^ 1, x3)
            return (x3, y3)
        lam = F.mul(y1 ^ y2, F.inv(x1 ^ x2))
        x3 = F.sq(lam) ^ lam ^ x1 ^ x2 ^ self.a
        y3 = F.mul(lam, x1 ^ x3) ^ x3 ^ y1
        return (x3, y3)

    def neg(self, P):
        return (P[0], P[0] ^ P[1])


def run_cell(n, l, seed):
    rng = random.Random(f"l3-t0-{n}-{l}-{seed}")
    F = Field(n)
    a = rng.randrange(2)
    b = rng.randrange(1, 1 << n)
    E = Curve(F, a, b)
    T0 = (0, E.sb)
    assert E.on(T0)
    pts = []
    for x in range(1, 1 << l):
        pts.extend(E.lift(x))
    for P in pts:
        assert E.on(P)
    N = len(pts)

    # identity check x(T0 - S) = sqrt(b)/x(S) on a sample of pairs
    for _ in range(min(200, N * N)):
        P, Q = rng.choice(pts), rng.choice(pts)
        S = E.add(P, Q)
        if S is None or S[0] == 0:
            continue
        R = E.add(T0, E.neg(S))
        assert R is not None and E.on(R)
        assert R[0] == F.mul(E.sb, F.inv(S[0])), "translation identity failed"
        assert E.add(E.add(S, R), None) == T0 or E.add(S, R) == T0

    limit = 1 << l
    ordered = 0
    repeated = 0
    xsets = set()
    for P in pts:
        for Q in pts:
            S = E.add(P, Q)
            if S is None or S[0] == 0:
                continue  # Q = -P, or P + Q = T0 (then P3 = O)
            x3 = F.mul(E.sb, F.inv(S[0]))
            if x3 < limit:  # x3 in V; x3 != 0 since sqrt(b) != 0
                ordered += 1
                xs = tuple(sorted((P[0], Q[0], x3)))
                if len(set(xs)) < 3:
                    repeated += 1
                xsets.add(xs)
    # full verification of every found x-set by an independent group sum
    for xs in xsets:
        ok = False
        for P in E.lift(xs[0]):
            for Q in E.lift(xs[1]):
                for R in E.lift(xs[2]):
                    if E.add(E.add(P, Q), R) == T0:
                        ok = True
        assert ok, f"unverified x-set {xs}"
    return {
        "n": n, "l": l, "seed": seed, "modulus": hex(F.f), "a": a, "b": hex(b),
        "N": N, "ordered": ordered, "ordered_with_repeat": repeated,
        "xsets": len(xsets),
        "est_ordered": N ** 3 / 2 ** n,
        "est_xsets": N ** 3 / (12 * 2 ** n),
        "note_est_2^(3l-n)/6": 2 ** (3 * l - n) / 6,
    }


def main():
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    cells = [(n, l) for n in (11, 13, 15, 17, 19, 21, 23)
             for l in range((n + 1) // 3 - 1, (n + 2) // 3 + 1)
             if 3 * l - 2 <= n and l >= 3]
    rows = []
    for n, l in cells:
        for s in range(seeds):
            r = run_cell(n, l, s)
            rows.append(r)
            print(json.dumps(r), flush=True)
    return rows


if __name__ == "__main__":
    main()
