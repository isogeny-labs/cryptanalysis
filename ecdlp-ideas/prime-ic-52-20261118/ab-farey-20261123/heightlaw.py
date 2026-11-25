#!/usr/bin/env python3
"""
heightlaw.py — the target-height skew, with the degenerate case removed exactly.

selector.py showed that mean r(R) rises as the target's rational height falls.
That measurement is contaminated by the trivial case: if R is itself a factor
base element then {R, P, -P} is a relation for every P, so r(R) >= N/2 with no
additive structure involved.  The dump now carries an exact in-base bit per
target (ecell marks the dlog of every base point), so the law can be stated on
targets provably OUTSIDE the base, for all three shapes -- not on a height
proxy, which for the interval base is the wrong predicate.

Reported per cell: lift = mean r in the bucket / mean r over the subset, bucket
by h/B where h is the smallest B' with x(R) in X(B').
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
    off = 4 + 8 * n
    inbase = np.frombuffer(d[off:off + n], dtype=np.uint8).astype(np.int64) \
        if len(d) >= off + n else np.zeros(n, dtype=np.int64)
    h = open(hfile, "rb").read()
    hb = np.frombuffer(h[4:4 + n], dtype=np.uint8).astype(np.int64)
    os.remove(dump)                       # 128 MB at the 2^24 rung
    return n, cnt, hb, inbase


def table(cnt, hb, mask, B, tag, meta):
    r = cnt[mask]
    hh = hb[mask]
    ntot = int(mask.sum())
    mu = r.mean()
    sd2 = (r * r).mean() - mu * mu
    lb = np.floor(hh - math.log2(max(B, 1))).astype(np.int64)
    rows = []
    for b in np.unique(lb):
        msk = lb == b
        nb = int(msk.sum())
        if nb < 200:
            continue
        mub = r[msk].mean()
        sdb = math.sqrt(max(sd2, 1e-12) * (1 - nb / ntot) / nb)
        rows.append(dict(meta, subset=tag, log2_h_over_B=int(b),
                         h_range=[B * 2 ** int(b), B * 2 ** (int(b) + 1) - 1],
                         n=nb, frac=nb / ntot, mean_r=float(mub),
                         lift=float(mub / mu), z=float((mub - mu) / sdb),
                         mean_r_subset=float(mu)))
    return rows


def main():
    rows = []
    for (p, m, N) in CELLS:
        for shape in (0, 1, 2):
            n, cnt, hb, inbase = load(p, m, N, shape)
            cellj = json.load(open(os.path.join(RAW, f"cell_{p}_{m}_{N}_{shape}.json")))
            B = cellj.get("B_used") or int(math.sqrt(N * math.pi ** 2 / 12))
            meta = {"p": p, "bits": p.bit_length(), "m": m, "N": N, "B": B,
                    "shape": SHAPES[shape], "in_base_frac": float(inbase.mean())}
            base = (np.arange(n) != 0)
            rows += table(cnt, hb, base, B, "all", meta)
            rows += table(cnt, hb, base & (inbase == 0), B, "outside_base", meta)
            print(f"p=2^{p.bit_length()-1} m={m} N={N:<5} {SHAPES[shape]:>8} "
                  f"B={B:<5} in_base={inbase.mean():.2e}")
    json.dump(rows, open(os.path.join(RAW, "heightlaw.json"), "w"), indent=1)

    for subset in ("all", "outside_base"):
        print(f"\n=== lift vs h/B, subset = {subset} ===")
        for (p, m, N) in CELLS:
            for sh in ("interval", "farey", "random"):
                sel = [x for x in rows if x["p"] == p and x["m"] == m and
                       x["N"] == N and x["shape"] == sh and x["subset"] == subset
                       and -1 <= x["log2_h_over_B"] <= 4]
                if not sel:
                    continue
                print(f" p=2^{p.bit_length()-1} m={m} {sh:>8} B={sel[0]['B']:<5} "
                      + " ".join(f"{x['log2_h_over_B']:+d}:{x['lift']:.2f}"
                                 for x in sel))


if __name__ == "__main__":
    main()
