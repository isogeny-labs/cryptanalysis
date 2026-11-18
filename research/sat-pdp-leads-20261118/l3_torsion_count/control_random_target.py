#!/usr/bin/env python3
"""Control for the L3 count: same curves (same seed derivation), same factor
base, same enumeration, but the target is a random point R of the curve
instead of T0. Ordered triples P1+P2+P3 = R with x(Pi) in V \\ {0} are counted
exactly (P3 = R - P1 - P2, checked by full group arithmetic) and compared with
the same estimate N^3 / 2^n. For a non-torsion R there is no global sign
symmetry, so each x-set carries 6 ordered triples, not 12.
"""
import json, random, sys, collections
import count_t0_relations as m

def cell(n, l, seed):
    rng = random.Random(f"l3-t0-{n}-{l}-{seed}")
    F = m.Field(n); a = rng.randrange(2); b = rng.randrange(1, 1 << n)
    E = m.Curve(F, a, b)
    r2 = random.Random(f"l3-ctrl-{n}-{l}-{seed}")
    while True:  # random affine point with x outside V
        x = r2.randrange(1 << l, 1 << n); L = E.lift(x)
        if L: R = r2.choice(L); break
    pts = [P for x in range(1, 1 << l) for P in E.lift(x)]
    limit = 1 << l; obs = 0; xsets = set()
    for P in pts:
        for Q in pts:
            S = E.add(P, Q)
            P3 = E.add(R, E.neg(S)) if S is not None else R
            if P3 is None or P3[0] == 0 or P3[0] >= limit: continue
            assert E.add(E.add(P, Q), P3) == R
            obs += 1; xsets.add(tuple(sorted((P[0], Q[0], P3[0]))))
    N = len(pts)
    return {"n": n, "l": l, "seed": seed, "N": N, "obs_ordered": obs,
            "xsets": len(xsets), "est_ordered": N ** 3 / 2 ** n}

seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 40
cells = [(n, l) for n in (11, 13, 15, 17, 19, 21, 23)
         for l in range((n + 1) // 3 - 1, (n + 2) // 3 + 1) if 3 * l - 2 <= n and l >= 3]
tot = collections.Counter()
for n, l in cells:
    for s in range(seeds):
        r = cell(n, l, s); print(json.dumps(r), flush=True)
        tot["obs"] += r["obs_ordered"]; tot["est"] += r["est_ordered"]; tot["xs"] += r["xsets"]
print(json.dumps({"pooled_obs_ordered": tot["obs"], "pooled_est_ordered": tot["est"],
                  "pooled_xsets": tot["xs"], "pooled_est_xsets": tot["est"] / 6}))
