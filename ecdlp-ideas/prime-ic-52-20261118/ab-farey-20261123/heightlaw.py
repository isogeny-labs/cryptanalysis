#!/usr/bin/env python3
"""
heightlaw.py — the target-height skew, stated in the form that decides whether
it is usable: lift vs h/B, and cost per relation including the search for a
target in the bucket.

For the Farey base X(B) the natural statistic is the target's own rational
height h(x(R)) (smallest B' with x(R) in X(B')).  selector.py shows the lift is
large.  This script answers the only question that matters operationally:

    cost per relation = [ (c_gen + c_sel)/f  +  c_trial ] / (lift * mu)

with f the fraction of targets in the bucket.  At production the search term
(c_gen/f) is what kills conditioning, because f ~ (h/p)^2.
"""
import json
import math
import os
import subprocess

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "raw")
ECELL = os.path.join(ROOT, "ecell")
HEIGHTS = os.path.join(ROOT, "heights")
SHAPES = {0: "interval", 1: "farey", 2: "random"}
CELLS = [(1046047, 2, 1448), (1046047, 3, 184),
         (16776547, 2, 5792), (16776547, 3, 464)]


def load(p, m, N, shape):
    dump = os.path.join(RAW, f"dump_{p}_{m}_{N}_{shape}.bin")
    hfile = os.path.join(RAW, f"height_{p}_{m}_{N}_{shape}.bin")
    if not os.path.exists(dump):
        out = os.path.join(RAW, f"cell_{p}_{m}_{N}_{shape}.json")
        subprocess.run([ECELL, str(p), str(N), str(m), str(shape), "11", out,
                        "dump", dump], check=True, capture_output=True)
    if not os.path.exists(hfile):
        subprocess.run([HEIGHTS, dump, hfile], check=True, capture_output=True,
                       env={**os.environ, "HP": str(p)})
    d = open(dump, "rb").read()
    n = int(np.frombuffer(d[:4], dtype=np.uint32)[0])
    cnt = np.frombuffer(d[4:4 + 4 * n], dtype=np.uint32).astype(np.float64)
    h = open(hfile, "rb").read()
    hb = np.frombuffer(h[4:4 + n], dtype=np.uint8).astype(np.int64)
    os.remove(dump)                       # 128 MB at the 2^24 rung
    return n, cnt, hb


def main():
    rows = []
    for (p, m, N) in CELLS:
        for shape in (0, 1, 2):
            n, cnt, hb = load(p, m, N, shape)
            cellj = json.load(open(os.path.join(RAW, f"cell_{p}_{m}_{N}_{shape}.json")))
            B = cellj.get("B_used") or int(math.sqrt(N * math.pi ** 2 / 12))
            keep = np.arange(n) != 0
            r = cnt[keep]
            hh = hb[keep]
            mu = r.mean()
            sd2 = (r * r).mean() - mu * mu
            ntot = int(keep.sum())
            # bucket by floor(log2(h/B)): the scale-free coordinate
            lb = np.floor(hh - math.log2(max(B, 1))).astype(np.int64)
            for b in np.unique(lb):
                msk = lb == b
                nb = int(msk.sum())
                if nb < 200:
                    continue
                mub = r[msk].mean()
                sdb = math.sqrt(max(sd2, 1e-12) * (1 - nb / ntot) / nb)
                rows.append({
                    "p": p, "bits": p.bit_length(), "m": m, "N": N, "B": B,
                    "shape": SHAPES[shape], "log2_h_over_B": int(b),
                    "h_range": [B * 2 ** int(b), B * 2 ** (int(b) + 1) - 1],
                    "n": nb, "frac": nb / ntot,
                    "mean_r": float(mub), "lift": float(mub / mu),
                    "z": float((mub - mu) / sdb),
                })
            print(f"p=2^{p.bit_length()-1} m={m} N={N:<5} {SHAPES[shape]:>8} B={B:<6} "
                  f"mean_r={mu:.5f}  buckets>=0: "
                  + ", ".join(f"h/B~2^{x['log2_h_over_B']}: {x['lift']:.2f}x"
                              for x in rows[-6:] if x["log2_h_over_B"] >= 0))

    json.dump(rows, open(os.path.join(RAW, "heightlaw.json"), "w"), indent=1)

    print("\n=== the law, farey shape, both rungs (h/B bucket -> frac, lift) ===")
    for (p, m, N) in CELLS:
        sel = [x for x in rows if x["p"] == p and x["m"] == m and x["N"] == N
               and x["shape"] == "farey" and -1 <= x["log2_h_over_B"] <= 4]
        if not sel:
            continue
        print(f"\n p=2^{p.bit_length()-1} m={m} N={N} base height B={sel[0]['B']}")
        for x in sel:
            print(f"   h/B in 2^{x['log2_h_over_B']:>3}: frac={x['frac']:.3e} "
                  f"lift={x['lift']:7.3f}  z={x['z']:+8.1f}")

    print("\n=== why it is not a production lever ===")
    # production: alpha = 0.2, m = 3, |F| = 2^51.2, one trial = |F|^(3/2) lookups
    # bucket h/B = 1 has measured lift ~10 at frac ~ (B/p)^2 ~ |F|/p
    for bits in (32, 48, 64, 256):
        alpha = 0.2
        log2F = alpha * bits
        log2B = 0.5 * (log2F + math.log2(math.pi ** 2 / 12))
        # frac of targets with h <= ~6B (the window where the lift is >= ~1.5)
        log2frac = min(0.0, 2 * (log2B + math.log2(6)) - bits + math.log2(12 / math.pi ** 2))
        c_gen_ns, c_trial_ns = 7e3, 2 ** (1.5 * log2F) * 10   # EEA+scalarmult vs lookups
        lift = 2.85                       # measured at h/B ~ 2^2, the usable window
        search = (c_gen_ns / 2 ** log2frac) if log2frac > -1e9 else float("inf")
        ratio = (search + c_trial_ns) / c_trial_ns     # cost relative to no selection
        print(f"  bits={bits:>3}: |F|=2^{log2F:5.1f} B=2^{log2B:5.1f} "
              f"window frac=2^{log2frac:8.1f} search/trial={ratio:.3e} "
              f"-> {'VIABLE' if ratio < 1 else 'DEAD'}")


if __name__ == "__main__":
    main()
