#!/usr/bin/env python3
"""Search for 40-bit Montgomery curves E: y^2 = x^3 + A x^2 + x over F_p
(B=1) with:
  - "weak": #E(F_p) = 4*q, q prime (cofactor-4 near-prime order -- Montgomery
    curves of the form y^2=x^3+Ax^2+x always have 4 | #E, same as
    Curve25519's cofactor 8 / X448's cofactor 4), and the quadratic twist
    order t = 2p+2-#E is B-smooth.
  - "secure": #E(F_p) = 4*q, q prime, and t is NOT fully B-smooth (has a
    large prime factor), the realistic twist-secure case.

Montgomery form is required because the x-only ladder's xDBL/xADD formulas
depend only on A, not on the curve's "B" (quadratic-twist) parameter -- so
the same ladder code computes correctly on E and on its twist E' without any
validation of the input x. Order is computed via PARI's ellcard (cypari2);
factoring via PARI's factor().
"""
from __future__ import annotations
import json, random, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from ec_leakage import is_probable_prime

import cypari2
pari = cypari2.Pari()


def pari_factor(n: int) -> dict:
    if n <= 1:
        return {}
    f = pari.factor(n)
    out = {}
    for i in range(f.nrows()):
        out[int(f[i, 0])] = int(f[i, 1])
    return out


def is_B_smooth(n: int, B: int):
    fac = pari_factor(n)
    return all(q <= B for q in fac), fac


def ellcard_mont(p: int, A: int) -> int:
    E = pari.ellinit([0, A, 0, 1, 0], p)
    return int(pari.ellcard(E))


def nonresidue(p: int, rng: random.Random) -> int:
    while True:
        d = rng.randrange(2, p)
        if pow(d, (p - 1) // 2, p) == p - 1:
            return d


def random_prime(bits: int, rng: random.Random) -> int:
    lo, hi = 1 << (bits - 1), 1 << bits
    while True:
        p = rng.randrange(lo, hi) | 1
        if is_probable_prime(p):
            return p


def find_curve(bits: int, B: int, rng: random.Random, want_smooth: bool, max_tries: int = 40000):
    for _ in range(max_tries):
        p = random_prime(bits, rng)
        d = nonresidue(p, rng)
        tries = 0
        inner_budget = 4000
        while tries < inner_budget:
            tries += 1
            A = rng.randrange(2, p)
            if (A * A - 4) % p == 0:
                continue  # A^2-4 == 0 degenerate
            n = ellcard_mont(p, A)
            if n % 4 != 0:
                continue
            q = n // 4
            if not is_probable_prime(q):
                continue
            t = 2 * p + 2 - n
            smooth, fac = is_B_smooth(t, B)
            if smooth == want_smooth:
                return dict(p=p, A=A, d=d, n=n, q=q, twist_order=t,
                            twist_factors={str(k): v for k, v in fac.items()},
                            tries=tries)
        # try a new p
    return None


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 20261114
    bits = 40
    B = 1 << 16
    rng = random.Random(seed)
    print("Searching for weak-twist curve (bits=%d, B=%d)..." % (bits, B))
    weak = find_curve(bits, B, rng, want_smooth=True)
    print(json.dumps(weak, indent=2))
    print("Searching for twist-secure curve...")
    secure = find_curve(bits, B, rng, want_smooth=False)
    print(json.dumps(secure, indent=2))
    out = dict(seed=seed, bits=bits, smooth_bound=B, weak=weak, secure=secure)
    with open(os.path.join(os.path.dirname(__file__), "curves_found.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("wrote curves_found.json")
