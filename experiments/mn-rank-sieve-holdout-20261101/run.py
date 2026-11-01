#!/usr/bin/env python3
"""Held-out-prime control for a Mestre-Nagao (MN) rank sieve.

Question: do two speed-ups proposed for an MN screen of the one-parameter
family E_t: y^2 = x^3 + (t^2-3)x + (t^3+5) -- early abort and residue-class
pruning mod 5..23 -- enrich anything beyond the score they are filtered on?

Control: score every curve a second time over primes disjoint from the screen
(401..1193). A curve with elevated rank has elevated MN sums at all primes, so
real enrichment must survive on the held-out primes.  Positive control: a
family with generic rank >= 1 (point (0,t) on y^2 = x^3 + (t^2-3)x + t^2) must
show a higher held-out mean than the test family, proving the instrument sees
rank.  Exploratory/retrospective: protocol and result are published together.
"""
import hashlib, json, math, platform, sys, time
import numpy as np

N = 10_000_000          # t = 1..N
TOP = 1e-5              # "best curves" = top 1 in 100,000 by screen score
SCREEN_LO, SCREEN_HI, HOLD_HI = 5, 400, 1200
PRUNE_PRIMES = [5, 7, 11, 13, 17, 19, 23]

def primes(a, b):
    return [p for p in range(max(a, 2), b) if all(p % q for q in range(2, int(p**.5) + 1))]

SCREEN = primes(SCREEN_LO, SCREEN_HI)
HOLD = primes(SCREEN_HI, HOLD_HI)

FAMILIES = {   # name -> (a(t), b(t)) as integer polynomials
    "test":     (lambda t: t * t - 3, lambda t: t**3 + 5),
    "posctl_r1": (lambda t: t * t - 3, lambda t: t * t),   # (0,t) is a point
}

def table(l, fam):
    """MN term -a_l(t) log l / l for every residue t mod l (0 at bad reduction)."""
    fa, fb = FAMILIES[fam]
    x = np.arange(l)
    chi = -np.ones(l, np.int64); chi[(x * x) % l] = 1; chi[0] = 0
    t = np.arange(l, dtype=np.int64)[:, None]
    a, b = fa(t) % l, fb(t) % l
    ap = -chi[(x[None, :] ** 3 + a * x[None, :] + b) % l].sum(1)
    ap = np.where(((4 * a**3 + 27 * b**2) % l)[:, 0] == 0, 0, ap)
    return (-ap * math.log(l) / l).astype(np.float32)

def naive(t, ps, fam):
    fa, fb = FAMILIES[fam]; s = 0.0
    for l in ps:
        a, b = fa(t) % l, fb(t) % l
        if (4 * a**3 + 27 * b * b) % l == 0:
            continue
        ap = 0
        for x in range(l):
            v = (x**3 + a * x + b) % l
            if v:
                ap -= 1 if pow(v, (l - 1) // 2, l) == 1 else -1
        s += -ap * math.log(l) / l
    return s

def score(T, ps, tabs):
    s = np.zeros(len(T), np.float32)
    for l in ps:
        s += tabs[l][T % l]
    return s

def main():
    out = {"schema": "mn-rank-sieve-holdout/v1", "status": "exploratory (retrospective)",
           "params": {"N": N, "top_fraction": TOP, "screen_primes": [SCREEN[0], SCREEN[-1], len(SCREEN)],
                      "holdout_primes": [HOLD[0], HOLD[-1], len(HOLD)], "prune_primes": PRUNE_PRIMES},
           "host": {"python": sys.version.split()[0], "numpy": np.__version__,
                    "machine": platform.machine(), "processor": platform.processor()},
           "source_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest()}
    t0 = time.perf_counter()
    tabs = {f: {l: table(l, f) for l in SCREEN + HOLD} for f in FAMILIES}
    out["table_build_s"] = time.perf_counter() - t0

    # correctness: fast == naive
    Tc = np.arange(1, 301, dtype=np.int64)
    t0 = time.perf_counter(); nv = np.array([naive(int(t), SCREEN, "test") for t in Tc])
    naive_us = (time.perf_counter() - t0) / len(Tc) * 1e6
    out["max_abs_naive_minus_fast"] = float(np.abs(nv - score(Tc, SCREEN, tabs["test"])).max())
    out["naive_us_per_curve"] = naive_us

    T = np.arange(1, N + 1, dtype=np.int64)
    t0 = time.perf_counter(); S = score(T, SCREEN, tabs["test"])
    out["fast_ns_per_curve_untiled_gather"] = (time.perf_counter() - t0) / N * 1e9
    SH = score(T, HOLD, tabs["test"])
    k = int(N * TOP); top = np.argsort(-S)[:k]
    out["top_k"] = k
    out["holdout_all"] = {"mean": float(SH.mean()), "sd": float(SH.std())}
    out["holdout_top_by_screen"] = {"mean": float(SH[top].mean()),
                                    "se": float(SH[top].std(ddof=1) / math.sqrt(k))}
    out["corr_screen_holdout"] = float(np.corrcoef(S, SH)[0, 1])

    thrH = np.quantile(SH, 1 - 1e-3)
    def holdout_enrich(mask):
        return float((SH[mask] >= thrH).mean() / 1e-3)

    S25 = score(T, SCREEN[:25], tabs["test"]); keep = S25 >= np.quantile(S25, 0.99)
    out["early_abort"] = {"first_primes": 25, "keep": 0.01, "recall_vs_screen": float(keep[top].mean()),
                          "holdout_top0.1pct_enrichment": holdout_enrich(keep)}

    out["pruning"] = []
    for f in (0.4, 0.6, 0.8):
        m = np.ones(N, bool)
        for l in PRUNE_PRIMES:
            good = np.argsort(-tabs["test"][l])[:max(1, round(f * l))]
            m &= np.isin(T % l, good)
        frac, rec = float(m.mean()), float(m[top].mean())
        out["pruning"].append({"keep_fraction": f, "space_fraction": frac, "recall_vs_screen": rec,
                               "yield_per_compute_vs_screen": rec / frac,
                               "holdout_top0.1pct_enrichment": holdout_enrich(m),
                               "holdout_mean_kept": float(SH[m].mean())})

    # positive control: generic rank >= 1 family must have higher held-out mean
    Tp = np.arange(1, 1_000_001, dtype=np.int64)
    pc = {}
    for f in FAMILIES:
        h = score(Tp, HOLD, tabs[f]); pc[f] = {"mean": float(h.mean()), "se": float(h.std(ddof=1) / 1000)}
    out["positive_control_holdout_mean_t_le_1e6"] = pc
    json.dump(out, open("result.json", "w"), indent=2)
    np.save("/tmp/_mn_scatter.npy", np.stack([S[:200000], SH[:200000]]))
    np.save("/tmp/_mn_top.npy", SH[top])
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
