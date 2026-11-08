#!/usr/bin/env python3
"""Numeric sanity checks for the base-point / arithmetic-progression note.

Toy prime-order curve y^2 = x^3 - 3x + b over F_p (24-bit p), the same shape
as crypto's generator-effect study. Everything is exact and seeded; nothing
here is a measurement of record. Run: python3 sanity.py > sanity.out
"""
import json, random, sys
from collections import Counter

# c1 of crypto/research/generator_effect_ic_20261019/DRYRUN.md
p, a, b, r = 8582641, -3, 6723661, 8580037

def add(P, Q):
    if P is None: return Q
    if Q is None: return P
    (x1, y1), (x2, y2) = P, Q
    if x1 == x2 and (y1 + y2) % p == 0: return None
    lam = ((3 * x1 * x1 + a) * pow(2 * y1, -1, p)) % p if P == Q else ((y2 - y1) * pow(x2 - x1, -1, p)) % p
    x3 = (lam * lam - x1 - x2) % p
    return (x3, (lam * (x1 - x3) - y1) % p)

def mul(k, P):
    R, A = None, P
    while k:
        if k & 1: R = add(R, A)
        A = add(A, A); k >>= 1
    return R

def sqrt_mod(n):
    # p % 4 == 1 here, so Tonelli-Shanks
    if pow(n, (p - 1) // 2, p) != 1: return None
    q, s = p - 1, 0
    while q % 2 == 0: q //= 2; s += 1
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1: z += 1
    m, c, t, R = s, pow(z, q, p), pow(n, q, p), pow(n, (q + 1) // 2, p)
    while t != 1:
        i, tt = 0, t
        while tt != 1: tt = tt * tt % p; i += 1
        bb = pow(c, 1 << (m - i - 1), p)
        m, c, t, R = i, bb * bb % p, t * bb * bb % p, R * bb % p
    return R

def point_with_x(x0):
    x = x0
    while True:
        y = sqrt_mod((x ** 3 + a * x + b) % p)
        if y is not None: return (x, y)
        x += 1

out = {"curve": {"p": p, "a": a, "b": b, "r": r}}
P = point_with_x(1)
assert mul(r, P) is None and mul(1, P) == P, "r is not the order of P"
rng = random.Random(20261108)

# 1. transfer identity: (k * c^-1 mod r) * (c*P) == k*P for random k, c
ok = 0
for _ in range(200):
    k, c = rng.randrange(1, r), rng.randrange(1, r)
    cinv = pow(c, -1, r)
    ok += mul(k * cinv % r, mul(c, P)) == mul(k, P)
out["transfer_identity_checks"] = {"trials": 200, "passed": ok}

# 2. arithmetic progression of scalars: constant difference, known shift
k, d = rng.randrange(1, r), rng.randrange(1, r)
Qs = [mul((k + i * d) % r, P) for i in range(50)]
D = mul(d, P)
out["ap_constant_difference"] = all(add(Qs[i + 1], (Qs[i][0], (-Qs[i][1]) % p)) == D for i in range(49))
out["ap_known_shift"] = all(Qs[i] == add(Qs[0], mul(i, D)) for i in range(50))

# 3. x-coordinates along an arithmetic progression of scalars vs i.i.d. random scalars:
#    equidistribution of x / p into 16 bins (chi-square) and lag-1 rank correlation.
def xs_stats(xs):
    n = len(xs); bins = Counter(int(16 * x / p) for x in xs)
    chi2 = sum((bins.get(i, 0) - n / 16) ** 2 / (n / 16) for i in range(16))
    ranks = {v: i for i, v in enumerate(sorted(xs))}
    rk = [ranks[x] for x in xs]
    mu = (n - 1) / 2
    num = sum((rk[i] - mu) * (rk[i + 1] - mu) for i in range(n - 1))
    den = sum((v - mu) ** 2 for v in rk)
    return {"n": n, "chi2_16bins_df15": round(chi2, 2), "lag1_rank_corr": round(num / den, 4)}
N = 4000
ap_xs = [mul((k + i * d) % r, P)[0] for i in range(N)]
rand_xs = [mul(rng.randrange(1, r), P)[0] for _ in range(N)]
out["x_distribution"] = {"arithmetic_progression_scalars": xs_stats(ap_xs), "iid_random_scalars": xs_stats(rand_xs),
                         "note": "chi-square with 15 df: mean 15, 95th percentile 25.0"}

# 4. sumset collapse: distinct pairwise sums of a progression base {[1]P..[B]P} vs a random base of B points
B = 205
prog = [mul(i, P) for i in range(1, B + 1)]
rand_scalars = rng.sample(range(1, r), B)
randb = [mul(s, P) for s in rand_scalars]
def sumset_size(base):
    S = set()
    for i in range(len(base)):
        for j in range(i, len(base)):
            Q = add(base[i], base[j]); S.add(Q)
    return len(S)
out["sumset_B205"] = {"progression_base_distinct_sums": sumset_size(prog), "progression_bound_2B_minus_1": 2 * B - 1,
                      "random_base_distinct_sums": sumset_size(randb), "unordered_pairs_with_repetition": B * (B + 1) // 2}
json.dump(out, sys.stdout, indent=2); print()
