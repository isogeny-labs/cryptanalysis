#!/usr/bin/env python3
"""
selector.py — is there a CHEAP statistic of the target that predicts how many
relations it has?

The counting identity in report.md section 3 fixes the mean of r(R) over the
group.  It says nothing about *conditioning*: if a statistic phi(R) that costs
a few cycles predicts r(R), the relation search can accept only targets with
high phi.  Conditioning is almost free because one trial costs |F|^{ceil(m/2)}
operations and phi costs tens of cycles, so even a 1% lift is a 1% speedup:

    cost per relation  ~  c_trial / (mean r | phi good)

That makes the lift threshold effectively 1.0, not 1/fraction.  This script
measures the lift for a family of cheap statistics, with an analytic null
(r is exchangeable across targets under "no correlation"), so a sub-percent
effect is testable.

Features
  half        x(R) < p/2                     (1 comparison)
  v2          trailing zeros of x(R)         (1 instruction)
  mod3, mod5  x(R) mod a small prime         (1 multiply)
  legendre    chi(x(R))                      (1 Euler exponentiation)
  log2x       floor(log2 x(R)) bucketed      (few instructions)
  log2height  rational height of x(R): the smallest B with x = a/b,
              |a|,|b| <= B  (EEA, 135 steps at 256 bits)

Usage: python3 selector.py [cell ...]
"""
import json
import math
import os
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "raw")
ECELL = os.path.join(ROOT, "ecell")


def dump_path(p, m, N, shape):
    return os.path.join(RAW, f"dump_{p}_{m}_{N}_{shape}.bin")


def ensure_dump(p, n, m, N, shape, seed=11):
    path = dump_path(p, m, N, shape)
    if not os.path.exists(path):
        out = os.path.join(RAW, f"cell_{p}_{m}_{N}_{shape}.json")
        cmd = [ECELL, str(p), str(N), str(m), str(shape), str(seed), out,
               "dump", path]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(r.stderr)
    d = open(path, "rb").read()
    n_ = int(np.frombuffer(d[:4], dtype=np.uint32)[0])
    cnt = np.frombuffer(d[4:4 + 4 * n_], dtype=np.uint32).astype(np.float64)
    xs = np.frombuffer(d[4 + 4 * n_:4 + 8 * n_], dtype=np.uint32).astype(np.int64)
    return n_, cnt, xs


# ---------------------------------------------------------------- height
def heights_bins(p, dump):
    """floor(log2 h(x)) per dlog, computed by heights.c (EEA, exact)."""
    out = dump.replace("dump_", "height_")
    if not os.path.exists(out):
        r = subprocess.run([os.path.join(ROOT, "heights"), dump, out],
                           capture_output=True, text=True,
                           env={**os.environ, "HP": str(p)})
        if r.returncode != 0:
            raise RuntimeError(r.stderr)
    d = open(out, "rb").read()
    n_ = int(np.frombuffer(d[:4], dtype=np.uint32)[0])
    return np.frombuffer(d[4:4 + n_], dtype=np.uint8).astype(np.int64)


def base_height_equiv(N):
    """Height of a Farey base with the same number of points: 4*Phi(B) ~ N."""
    return int(math.sqrt(N * math.pi ** 2 / 12))


def features(p, xs):
    """Cheap statistics, each returned as an integer bucket id."""
    out = {}
    out["half"] = (xs >= p // 2).astype(np.int64)
    v = xs.copy()
    v2 = np.zeros_like(v)
    for _ in range(20):
        m = (v % 2 == 0) & (v > 0)
        v2 += m
        v = np.where(m, v // 2, v)
    out["v2"] = np.minimum(v2, 6)
    out["mod3"] = xs % 3
    out["mod5"] = xs % 5
    out["log2x"] = np.floor(np.log2(np.maximum(xs, 1))).astype(np.int64) // 4
    return out


def legendre_buckets(p, xs):
    # chi(x) for x != 0; Euler's criterion (slow, done once)
    out = np.zeros_like(xs)
    for i, xv in enumerate(xs):
        if xv == 0:
            out[i] = 0
        else:
            out[i] = 1 if pow(int(xv), (p - 1) // 2, p) == 1 else 2
    return out


# ---------------------------------------------------------------- stats
def bucket_table(cnt, r, buckets, label, n_total):
    """mean r per bucket, lift, analytic null z, and Sidak-corrected p."""
    mu = r.sum() / n_total
    sd2 = (r * r).sum() / n_total - mu * mu
    rows = []
    ids = np.unique(buckets)
    for b in ids:
        m_ = buckets == b
        nb = int(m_.sum())
        if nb < 100:
            continue
        mub = r[m_].mean()
        # null: sampling nb of the n_total r-values without replacement
        sd_b = math.sqrt(max(sd2, 1e-12) * (1 - nb / n_total) / nb)
        z = (mub - mu) / sd_b
        rows.append({
            "bucket": int(b), "n": nb, "frac": nb / n_total,
            "mean_r": mub, "lift": mub / mu, "z": z,
            "frac_times_lift": (nb / n_total) * (mub / mu),
        })
    rows.sort(key=lambda r_: -r_["lift"])
    k = max(len(rows), 1)
    for r_ in rows:
        r_["p_sidak"] = 1 - (1 - 2 * (1 - _ncdf(abs(r_["z"])))) ** k
    return {"feature": label, "mu": mu, "sd": math.sqrt(max(sd2, 1e-12)),
            "buckets": rows}


def _ncdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def main():
    cells = [(1046047, 1046779, 2, 1448), (1046047, 1046779, 3, 184),
             (16776547, 16769119, 2, 5792), (16776547, 16769119, 3, 464)]
    report = []
    for (p, n, m, N) in cells:
        for shape in (0, 1, 2):
            n_, cnt, xs = ensure_dump(p, n, m, N, shape)
            keep = np.arange(n_) != 0          # drop R = O
            r = cnt[keep]
            xk = xs[keep]
            n_total = int(keep.sum())
            feats = features(p, xk)
            hb = heights_bins(p, dump_path(p, m, N, shape))[keep]
            feats["log2height"] = hb
            # R in the base at the equivalent Farey height is the degenerate
            # case (a target that is already a base element); mark it -1 so
            # the outside-base lift can be read separately.
            feats["log2height_outside_base"] = np.where(
                hb > math.log2(max(base_height_equiv(N), 1)), hb, -1)
            if p == 1046047:
                feats["legendre"] = legendre_buckets(p, xk)
            for name, b in feats.items():
                t = bucket_table(cnt[keep], r, b, name, n_total)
                t.update({"p": p, "m": m, "N": N, "shape": shape})
                report.append(t)
            best = max((b["lift"] for t in report[-len(feats):] for b in t["buckets"]),
                       default=1.0)
            print(f"p={p} m={m} N={N} shape={shape}  base mean r={r.mean():.5f} "
                  f"sd={r.std():.4f}  best lift among features={best:.4f}")
            # the dumps are 128 MB each at the 2^24 rung; keep only the
            # 1-byte-per-target height file, which the trend table needs.
            try:
                os.remove(dump_path(p, m, N, shape))
            except OSError:
                pass
    json.dump(report, open(os.path.join(RAW, "selector.json"), "w"), indent=1)

    print("\n=== top lifts (all cells/features), with Sidak p ===")
    flat = [(t["p"], t["m"], t["N"], t["shape"], t["feature"], b)
            for t in report for b in t["buckets"]]
    flat.sort(key=lambda z: -z[5]["lift"])
    for (p, m, N, sh, f, b) in flat[:18]:
        print(f"p={p:>8} m={m} N={N:<5} shape={sh} {f:<11} bucket={b['bucket']:>3} "
              f"frac={b['frac']:.3f} lift={b['lift']:.4f} z={b['z']:+.2f} "
              f"p_sidak={b['p_sidak']:.3f}")

    # replication: does the sign of the best binary split repeat across shapes?
    print("\n=== replication of the strongest split (half: x < p/2) ===")
    for t in report:
        if t["feature"] != "half":
            continue
        rows = {b["bucket"]: b for b in t["buckets"]}
        if 0 in rows and 1 in rows:
            print(f"p={t['p']:>8} m={t['m']} N={t['N']:<5} shape={t['shape']}  "
                  f"lift(low half)={rows[0]['lift']:.4f}  lift(high)={rows[1]['lift']:.4f}")


if __name__ == "__main__":
    main()
