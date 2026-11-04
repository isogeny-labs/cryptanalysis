#!/usr/bin/env python3
"""Analysis frozen with PROTOCOL.md. Reads rows_<arm>_<part>.jsonl.gz (parts p1, p2) from this directory,
checks the invariants, writes results.json and results.md. Exits non-zero, writing nothing, if any invariant fails."""
from __future__ import annotations

import glob
import gzip
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SEED = 20261102
TEST_ARMS = ["r64", "r128"]                    # decision arms, full grid
SIZES = [42, 44, 46]
GRID = {42: 1600, 44: 1130, 46: 800}   # curves per family; one target per curve
CTRL_R32 = 100                                 # identity control: r32 on curves 0..99 of every 42-bit cell
CTRL_R8 = 200                                  # positive control: r8 on curves 0..199 of every 42-bit cell
RHO_N = 150                                    # rho reference on main for curves 0..149 of every cell
FAMS = ["j1728", "j0"]
M = {"j1728": 4, "j0": 6}
B = 10000
K_PRIMARY = 2                                  # r64 and r128, both families pooled
K_ALL = 6                                      # primary 2 + family-alone 4
Z = {  # two-sided normal quantiles are not used; bootstrap percentile intervals at these coverages
    "primary": 1 - 0.05 / K_PRIMARY,           # 97.5% two-sided
    "family": 1 - 0.05 / K_ALL,                # 99.1667% two-sided
}


def auto_r(n: int, m: int) -> int:
    """main's table rule (src/curve.c, glv_rho_solve): c = 12, cap 32."""
    sqrt_nm = math.isqrt(n // m) + 1
    lg = n.bit_length()
    rbudget = sqrt_nm // (12 * lg)
    rr = 8
    while rr * 2 <= rbudget and rr * 2 <= 32:
        rr *= 2
    return rr


def load(arm):
    rows = {}
    files = sorted(glob.glob(str(HERE / f"rows_{arm}_p*.jsonl.gz")))
    if not files:
        sys.exit(f"no rows for {arm}")
    for f in files:
        for line in gzip.open(f, "rt"):
            x = json.loads(line)
            key = (x["family"], x["bits"], x["curve"], x["target"])
            if key in rows:
                sys.exit(f"duplicate row {arm} {key}")
            rows[key] = x
    return rows


def cell_arrays(A, Mr, fam, bits, n=None):
    n = n if n is not None else GRID[bits]
    a = np.array([A[(fam, bits, c, 0)]["ops"] for c in range(n)], float)
    m = np.array([Mr[(fam, bits, c, 0)]["ops"] for c in range(n)], float)
    return a, m


def boot_logratio(cells, rng):
    """cells: list of (a, m) arrays (same curves). Returns point estimate of the mean of log(sum a / sum m) over cells
    and B bootstrap replicates (curves resampled with replacement independently within each cell)."""
    pt = float(np.mean([math.log(a.sum() / m.sum()) for a, m in cells]))
    reps = np.zeros(B)
    for a, m in cells:
        n = len(a)
        idx = rng.integers(0, n, size=(B, n))
        reps += np.log(a[idx].sum(axis=1) / m[idx].sum(axis=1))
    return pt, reps / len(cells)


def interval(reps, cover):
    lo, hi = np.quantile(reps, [(1 - cover) / 2, 1 - (1 - cover) / 2])
    return float(math.exp(lo)), float(math.exp(hi))


def main() -> int:
    R = {a: load(a) for a in ["main", "r32", "r8"] + TEST_ARMS}
    mr = R["main"]
    fail = []
    for a, rows in R.items():
        bad = [k for k, x in rows.items() if not x["correct"]]
        if bad:
            fail.append(f"{a}: {len(bad)} wrong answers")
    want = {(f, b, c, 0) for f in FAMS for b in SIZES for c in range(GRID[b])}
    if set(mr) != want:
        fail.append("main: grid is not the frozen grid")
    wantr = {k for k in want if k[2] < RHO_N}
    got_rho = {k for k, x in mr.items() if "rho_ops" in x}
    if got_rho != wantr:
        fail.append("main: rho reference is not on exactly curves 0..RHO_N-1 of every cell")
    if any(not mr[k].get("rho_correct", False) for k in got_rho):
        fail.append("rho reference: wrong answers")
    wants = {"r32": {k for k in want if k[1] == 42 and k[2] < CTRL_R32},
             "r8": {k for k in want if k[1] == 42 and k[2] < CTRL_R8}}
    for a in TEST_ARMS + ["r32", "r8"]:
        w = want if a in TEST_ARMS else wants[a]
        if set(R[a]) != w:
            fail.append(f"{a}: grid differs from the frozen grid")
        for k, x in R[a].items():
            m = mr.get(k)
            if m and (m["p"], m["a"], m["b"], m["k"]) != (x["p"], x["a"], x["b"], x["k"]):
                fail.append(f"{a}: different curve or target at {k}")
                break
    mains_r = {auto_r(x["r"], M[k[0]]) for k, x in mr.items()}
    if mains_r != {32}:
        fail.append(f"main's rule picks {sorted(mains_r)}, not only 32 (protocol assumes 32)")
    ident = [k for k, x in R["r32"].items() if x["ops"] != mr[k]["ops"]]
    if ident:
        fail.append(f"identity control r32: {len(ident)} of {len(R['r32'])} rows differ from main")
    if fail:
        print("INVARIANT FAILURE:\n  " + "\n  ".join(fail))
        return 1

    out = {"seed": SEED, "bootstrap": B, "comparisons_primary": K_PRIMARY, "comparisons_all": K_ALL,
           "grid": GRID, "identity_control_r32": {"rows": len(R["r32"]), "differing": 0},
           "cells": {}, "primary": {}, "family": {}, "by_size": {}, "positive_control": {}}
    # per-cell descriptive: 95% interval, plus S and the gap to matched rho (curves 0..RHO_N-1)
    for fam in FAMS:
        for b in SIZES:
            n = GRID[b]
            keys = [(fam, b, c, 0) for c in range(n)]
            rk = [(fam, b, c, 0) for c in range(RHO_N)]
            cell = {"curves": n,
                    "main_S": float(np.mean([mr[k]["ops"] / math.sqrt(mr[k]["r"] / M[fam]) for k in keys])),
                    "rho_S": float(np.mean([mr[k]["rho_ops"] / math.sqrt(mr[k]["r"]) for k in rk])),
                    "main_over_rho": sum(mr[k]["ops"] for k in rk) / sum(mr[k]["rho_ops"] for k in rk), "arms": {}}
            for a in TEST_ARMS:
                rng = np.random.default_rng([SEED, hash_(a), M[fam], b])
                pt, reps = boot_logratio([cell_arrays(R[a], mr, fam, b)], rng)
                cell["arms"][a] = {"over_main": math.exp(pt), "ci95": interval(reps, 0.95),
                                   "over_rho": sum(R[a][k]["ops"] for k in rk) / sum(mr[k]["rho_ops"] for k in rk)}
            out["cells"][f"{fam}:{b}"] = cell
    # primary: pooled geometric mean of the six cell ratios, both families; K = 2 at 97.5% two-sided
    for a in TEST_ARMS:
        cells = [cell_arrays(R[a], mr, f, b) for f in FAMS for b in SIZES]
        pt, reps = boot_logratio(cells, np.random.default_rng([SEED, hash_(a), 0]))
        lo, hi = interval(reps, Z["primary"])
        out["primary"][a] = {"geomean_over_main": math.exp(pt), "ci": [lo, hi], "coverage": Z["primary"],
                             "half_width": (hi - lo) / 2 / math.exp(pt), "confirmed": hi < 1,
                             "ci95": interval(reps, 0.95)}
        # family alone: secondary, K = 6
        for fam in FAMS:
            cells = [cell_arrays(R[a], mr, fam, b) for b in SIZES]
            pt, reps = boot_logratio(cells, np.random.default_rng([SEED, hash_(a), 1, M[fam]]))
            lo, hi = interval(reps, Z["family"])
            out["family"][f"{a}:{fam}"] = {"geomean_over_main": math.exp(pt), "ci": [lo, hi], "coverage": Z["family"],
                                           "half_width": (hi - lo) / 2 / math.exp(pt), "confirmed": hi < 1}
        # descriptive per size, both families pooled
        for b in SIZES:
            cells = [cell_arrays(R[a], mr, f, b) for f in FAMS]
            pt, reps = boot_logratio(cells, np.random.default_rng([SEED, hash_(a), 2, b]))
            out["by_size"][f"{a}:{b}"] = {"geomean_over_main": math.exp(pt), "ci95": interval(reps, 0.95)}
    # positive control: r8 vs main on the same curves (42 bits, both families), ratio of sums per family, pooled
    cells = [cell_arrays(R["r8"], mr, f, 42, CTRL_R8) for f in FAMS]
    pt, reps = boot_logratio(cells, np.random.default_rng([SEED, 8, 0]))
    ci = interval(reps, 0.95)
    out["positive_control"] = {"r8_over_main_42": math.exp(pt), "ci95": ci, "pass": ci[0] > 1}
    (HERE / "results.json").write_text(json.dumps(out, indent=1) + "\n")

    L = ["| family | bits | curves | main S | rho S | main/rho | r64/main | r128/main |", "|---|---|---|---|---|---|---|---|"]
    f = lambda e: f"{e['over_main']:.3f} [{e['ci95'][0]:.3f}, {e['ci95'][1]:.3f}]"
    for key, c in out["cells"].items():
        fam, bits = key.split(":")
        L.append(f"| {fam} | {bits} | {c['curves']} | {c['main_S']:.3f} | {c['rho_S']:.3f} | {c['main_over_rho']:.3f} | "
                 + " | ".join(f(c["arms"][a]) for a in TEST_ARMS) + " |")
    L += ["", "Cell intervals are 95% bootstrap intervals, descriptive. S and main/rho use curves 0..149 of each cell for rho.", "",
          "Primary (both families, geometric mean of the six cell ratios, 97.5% interval, K = 2):", ""]
    L += [f"- {a}: {v['geomean_over_main']:.4f} [{v['ci'][0]:.4f}, {v['ci'][1]:.4f}], half-width {100 * v['half_width']:.2f}%, "
          f"{'CONFIRMED (upper bound below 1)' if v['confirmed'] else 'not confirmed'}" for a, v in out["primary"].items()]
    L += ["", "Secondary (one family alone, 99.167% interval, K = 6):", ""]
    L += [f"- {k}: {v['geomean_over_main']:.4f} [{v['ci'][0]:.4f}, {v['ci'][1]:.4f}], half-width {100 * v['half_width']:.2f}%, "
          f"{'confirmed' if v['confirmed'] else 'not confirmed'}" for k, v in out["family"].items()]
    L += ["", "Descriptive per size (both families, 95%):", ""]
    L += [f"- {k}: {v['geomean_over_main']:.4f} [{v['ci95'][0]:.4f}, {v['ci95'][1]:.4f}]" for k, v in out["by_size"].items()]
    pc = out["positive_control"]
    L += ["", f"Positive control (table 8 vs main, 42 bits, both families, 95%): {pc['r8_over_main_42']:.3f} "
          f"[{pc['ci95'][0]:.3f}, {pc['ci95'][1]:.3f}] pass={pc['pass']}"]
    (HERE / "results.md").write_text("Ratios of curve_solve group operations to main on the same targets.\n\n" + "\n".join(L) + "\n")
    print((HERE / "results.md").read_text())
    return 0


def hash_(s: str) -> int:
    return sum((i + 1) * ord(c) for i, c in enumerate(s))


if __name__ == "__main__":
    sys.exit(main())
