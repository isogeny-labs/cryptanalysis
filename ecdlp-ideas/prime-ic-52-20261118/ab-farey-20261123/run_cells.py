#!/usr/bin/env python3
"""
run_cells.py — drive ecell.c over the pre-registered cells, then reduce.

Every cell is one (p, m, shape) with the base normalised to N points, so all
shapes in a block have the same |F| and the same group.  Nothing is sampled:
r(R) is the exact representation function over the whole group.

Prints the comparison table and writes raw/cells.json plus raw/summary.json.
"""
import itertools
import json
import math
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "raw")
ECELL = os.path.join(ROOT, "ecell")
SHAPES = {0: "interval", 1: "farey", 2: "random"}

# p, n=#E  (both found by findprime.c: p = 3 mod 4, #E prime, E: y^2=x^3+7)
CELLS = []


def add_block(p, n, m, Ns, seeds=11):   # matches PROTOCOL.json's seed
    for N in Ns:
        for s in (0, 1, 2):
            CELLS.append((p, n, m, N, s, seeds))


def plan():
    p1, n1 = 1046047, 1046779          # 2^20 rung
    p2 = n2 = None
    pf = os.path.join(RAW, "prime24.txt")   # 2^24 rung, from findprime.c
    if os.path.exists(pf) and open(pf).read().split():
        p2, n2 = [int(v) for v in open(pf).read().split()[:2]]
    # m = 2 : mean r ~ N^2/(2n) ~ 1 at N ~ sqrt(2n)
    add_block(p1, n1, 2, [1448, 512])
    if p2:
        add_block(p2, n2, 2, [5792])
    # m = 3 : mean r ~ N^3/(6n) ~ 1 at N ~ (6n)^(1/3)
    add_block(p1, n1, 3, [184, 96])
    if p2:
        add_block(p2, n2, 3, [464])
    return CELLS


def run():
    out = []
    for i, (p, n, m, N, shape, seed) in enumerate(plan()):
        path = os.path.join(RAW, f"cell_{p}_{m}_{N}_{shape}.json")
        if not os.path.exists(path):
            cmd = [ECELL, str(p), str(N), str(m), str(shape), str(seed), path]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                print("FAIL", cmd, r.stderr.strip())
                continue
            print(r.stdout.strip())
        d = json.load(open(path))
        out.append(d)
    json.dump(out, open(os.path.join(RAW, "cells.json"), "w"), indent=1)
    return out


def choose2(k):
    return k * (k + 1) // 2


def choose3(k):
    return k * (k + 1) * (k + 2) // 6


def summarise(cells):
    """Group by (p, m, N) and compare shapes."""
    from collections import defaultdict
    groups = defaultdict(list)
    for c in cells:
        groups[(c["p"], c["m"], c["N"])].append(c)
    rows = []
    for (p, m, N), cs in sorted(groups.items()):
        n = cs[0]["n"]
        expect_tuples = choose2(N) if m == 2 else choose3(N)
        for c in cs:
            dO = c["r_at_O"]
            mean_x = c["sum_r_exclO"] / (n - 1)
            var_x = c["sum_r2_exclO"] / (n - 1) - mean_x ** 2
            rows.append({
                "p": p, "n": n, "m": m, "N": N, "shape": SHAPES[c["shape"]],
                "B_used": c.get("B_used", 0),
                "tuples": c["tuples"], "tuples_expected": expect_tuples,
                "tuples_ok": c["tuples"] == expect_tuples,
                "sum_ok": c["sum_r"] == expect_tuples,
                "r_at_O": dO, "r_at_O_pred": (N // 2 if m == 2 else None),
                "mean_exclO": round(mean_x, 6),
                "var_exclO": round(var_x, 6),
                "max_exclO": c["max_r_exclO"],
                "nz_exclO": c["nz_exclO"],
                "frac_targets_hit": round(c["nz_exclO"] / (n - 1), 6),
                "frac2": round(c["ge2_exclO"] / (n - 1), 6),
            })
    return rows


def jm_table():
    """H5: Jochemsz-May box product at equal |F|, interval vs rational height."""
    rows = []
    for m in (3, 4, 5, 6):
        d = 2 ** (m - 1)
        for log2p in (32, 128, 256):
            # alpha reachable under prod X_i^{d_i} < p^{2/(m+1)}
            def alpha_from_prod(log2prod):
                return (2 / (m + 1) - log2prod) / log2p
            # interval: m variables, bound X = |F| = p^a  -> log2 prod = m*d*a*log2p
            #   bound: m*d*a*log2p < 2/(m+1)*log2p  => a < 2/(m(m+1)d)
            a_int = 2 / (m * (m + 1) * d)
            # a/b: 2m variables, bound B = sqrt(|F|*pi^2/12)
            #   log2 prod = 2m*d*(a*log2p/2 + log2(sqrt(pi^2/12)))
            #   => m*d*a*log2p + 2m*d*log2(sqrt(pi^2/12)) < 2/(m+1)*log2p
            c = 2 * m * d * 0.5 * math.log2(math.pi ** 2 / 12)
            a_ab = (2 / (m + 1) * log2p - c) / (m * d * log2p)
            rows.append({
                "m": m, "d": d, "log2p": log2p,
                "alpha_JM_interval": a_int,
                "alpha_JM_ab": a_ab,
                "delta_alpha": a_ab - a_int,
                "delta_exponent_bits": (a_ab - a_int) * log2p,
            })
    return rows


if __name__ == "__main__":
    cells = run()
    rows = summarise(cells)
    jm = jm_table()
    json.dump(rows, open(os.path.join(RAW, "summary.json"), "w"), indent=1)
    json.dump(jm, open(os.path.join(RAW, "jm.json"), "w"), indent=1)

    print("\n=== exact yield, by (p, m, N) ===")
    hdr = f"{'p':>9} {'m':>2} {'N':>6} {'shape':>9} {'mean':>8} {'var':>8} " \
          f"{'max':>5} {'P(r>=1)':>8} {'P(r>=2)':>8} {'tuples_ok':>9}"
    print(hdr)
    for r in rows:
        print(f"{r['p']:>9} {r['m']:>2} {r['N']:>6} {r['shape']:>9} "
              f"{r['mean_exclO']:>8.4f} {r['var_exclO']:>8.4f} {r['max_exclO']:>5} "
              f"{r['frac_targets_hit']:>8.5f} {r['frac2']:>8.5f} {str(r['tuples_ok']):>9}")
    print("\n=== H5: Jochemsz-May alpha at equal |F| ===")
    for r in jm:
        print(f"m={r['m']} d={r['d']:>3} p=2^{r['log2p']:>3}  "
              f"a_int={r['alpha_JM_interval']:.6f} a_ab={r['alpha_JM_ab']:.6f} "
              f"delta_bits={r['delta_exponent_bits']:.5f}")
