#!/usr/bin/env python3
"""Coset-aware estimate for the L3 count, using chi(P) = Tr(x) + Tr(a)
(P in 2E(K) iff chi = 0 on y^2 + xy = x^3 + a x^2 + b, n odd).

1. Verifies the chi criterion on each cell: halving by brute force is too
   slow, so it checks the necessary consistency that chi is additive on
   random sums of factor-base points (chi(P+Q) = chi(P) + chi(Q)).
2. Counts N0, N1 = factor-base points by chi class.
3. Refined expected ordered triples: sum over (P1, P2) of
   N_{c} * 2 / 2^n, c = chi(T0) + chi(P1) + chi(P2) (P3 = T0 - P1 - P2 is
   heuristically uniform in its coset of 2E, which has about 2^(n-1) points).
4. Recounts observed relations from the same seeds and checks that every one
   satisfies chi(P1)+chi(P2)+chi(P3) = chi(T0).
Prints one JSON row per cell plus a pooled comparison.
"""
import json, random, sys, collections
import count_t0_relations as m

def chi(F, a, P):
    return F.trace(P[0]) ^ F.trace(a)

def cell(n, l, seed):
    rng = random.Random(f"l3-t0-{n}-{l}-{seed}")  # same derivation as the counter
    F = m.Field(n); a = rng.randrange(2); b = rng.randrange(1, 1 << n)
    E = m.Curve(F, a, b); T0 = (0, E.sb)
    pts = [P for x in range(1, 1 << l) for P in E.lift(x)]
    c = [chi(F, a, P) for P in pts]
    # additivity check on random sums (consistency of the criterion)
    r2 = random.Random(seed)
    for _ in range(300):
        i, j = r2.randrange(len(pts)), r2.randrange(len(pts))
        S = E.add(pts[i], pts[j])
        if S is None or S[0] == 0: continue
        assert chi(F, a, S) == c[i] ^ c[j], "chi not additive"
    cT0 = F.trace(a)  # Tr(0) + Tr(a)
    N = [c.count(0), c.count(1)]
    est = 0.0; obs = 0; parity_ok = True
    limit = 1 << l
    for i, P in enumerate(pts):
        for j, Q in enumerate(pts):
            need = cT0 ^ c[i] ^ c[j]
            est += N[need] * 2 / 2 ** n
            S = E.add(P, Q)
            if S is None or S[0] == 0: continue
            x3 = F.mul(E.sb, F.inv(S[0]))
            if x3 < limit:
                obs += 1
                R = E.add(T0, E.neg(S))
                if c[i] ^ c[j] ^ chi(F, a, R) != cT0: parity_ok = False
    return {"n": n, "l": l, "seed": seed, "a": a, "N0": N[0], "N1": N[1],
            "obs_ordered": obs, "est_naive": len(pts) ** 3 / 2 ** n,
            "est_coset": est, "parity_ok": parity_ok}

seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 40
cells = [(n, l) for n in (11, 13, 15, 17, 19, 21, 23)
         for l in range((n + 1) // 3 - 1, (n + 2) // 3 + 1) if 3 * l - 2 <= n and l >= 3]
tot = collections.Counter()
for n, l in cells:
    for s in range(seeds):
        r = cell(n, l, s)
        print(json.dumps(r), flush=True)
        tot["obs"] += r["obs_ordered"]; tot["naive"] += r["est_naive"]; tot["coset"] += r["est_coset"]
        tot["bad"] += (not r["parity_ok"])
print(json.dumps({"pooled_obs_ordered": tot["obs"], "pooled_est_naive": tot["naive"],
                  "pooled_est_coset": tot["coset"], "cells_with_parity_violation": tot["bad"]}))
