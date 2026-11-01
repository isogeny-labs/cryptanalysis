#!/usr/bin/env python3
"""Analysis and rule, frozen with PROTOCOL.md. Reads rows_<arm>_<part>.jsonl.gz (parts p1, p2) from this directory
(or --dir), checks the invariants, applies the frozen selection rule, writes results.json and results.md.
Exits non-zero, writing nothing, if any invariant fails."""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SEED = 20261105
SIZES = [38, 39, 40, 41, 42]
FAMS = ["j1728", "j0"]
M = {"j1728": 4, "j0": 6}
TEST_ARMS = ["r64", "r128"]
B = 10000
MARGIN = math.log(0.995)       # fitted saving required at every size from T up
UB_COVER = 0.90                # one-sided coverage of the go gate
TIE = 0.005                    # log-ratio tie width between r64 and r128 (smaller table wins ties)
GRID = 700                     # curves per cell (one target each)
IDENT = {38: 40, 42: 40}       # identity control r32: curves 0..n-1 of these sizes, both families
POS = {42: 100}                # positive control r8: curves 0..n-1 of these sizes, both families
CFG = {}


def auto_r(n: int, m: int, cap: int = 32) -> int:
    sqrt_nm = math.isqrt(n // m) + 1
    lg = n.bit_length()
    rbudget = sqrt_nm // (12 * lg)
    rr = 8
    while rr * 2 <= rbudget and rr * 2 <= cap:
        rr *= 2
    return rr


def load(d, arm):
    rows = {}
    files = sorted(glob.glob(str(d / f"rows_{arm}_p*.jsonl.gz")))
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


def arrays(A, Mr, fam, bits, n):
    a = np.array([A[(fam, bits, c, 0)]["ops"] for c in range(n)], float)
    m = np.array([Mr[(fam, bits, c, 0)]["ops"] for c in range(n)], float)
    return a, m


def hash_(s: str) -> int:
    return sum((i + 1) * ord(c) for i, c in enumerate(s))


def fit_T(L):
    """L: log-ratios at SIZES (array, last axis). OLS line on the size; T = smallest size b such that the fitted
    log-ratio is <= MARGIN at every size from b to the largest. None if there is none. Works on (..., 5) arrays."""
    x = np.array(SIZES, float)
    xc = x - x.mean()
    slope = (L * xc).sum(-1) / (xc ** 2).sum()
    fit = L.mean(-1)[..., None] + slope[..., None] * xc
    ok = fit <= MARGIN
    # suffix-all: ok[b..end] all true
    suf = np.flip(np.cumprod(np.flip(ok, -1), -1), -1).astype(bool)
    Ts = np.full(L.shape[:-1], -1)
    for i, b in enumerate(SIZES):
        first = suf[..., i] & (Ts == -1)
        Ts = np.where(first, b, Ts)
    return Ts, fit, slope


def interval(reps, cover):
    lo, hi = np.quantile(reps, [(1 - cover) / 2, 1 - (1 - cover) / 2])
    return float(math.exp(lo)), float(math.exp(hi))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(HERE))
    ap.add_argument("--grid", type=int, default=GRID, help="curves per cell (frozen value 700; smaller only for dry runs)")
    a_ = ap.parse_args()
    d = Path(a_.dir)
    n = a_.grid
    R = {a: load(d, a) for a in ["main", "r32", "r8"] + TEST_ARMS}
    mr = R["main"]
    fail = []
    for a, rows in R.items():
        bad = [k for k, x in rows.items() if not x["correct"]]
        if bad:
            fail.append(f"{a}: {len(bad)} wrong answers")
    want = {(f, b, c, 0) for f in FAMS for b in SIZES for c in range(n)}
    wants = {"r32": {k for k in want if k[1] in IDENT and k[2] < min(IDENT[k[1]], n)},
             "r8": {k for k in want if k[1] in POS and k[2] < min(POS[k[1]], n)}}
    for a in ["main"] + TEST_ARMS + ["r32", "r8"]:
        w = wants.get(a, want)
        if set(R[a]) != w:
            fail.append(f"{a}: grid differs from the frozen grid")
        for k, x in R[a].items():
            m = mr.get(k)
            if m and (m["p"], m["a"], m["b"], m["k"]) != (x["p"], x["a"], x["b"], x["k"]):
                fail.append(f"{a}: different curve or target at {k}")
                break
    if {auto_r(x["r"], M[k[0]]) for k, x in mr.items()} != {32}:
        fail.append("main's rule does not pick r = 32 for every curve")
    # forced r equals what a cap-C rule would pick on every n of these sizes: the uncapped budget is >= 128 at the smallest n
    for b in SIZES:
        for m in M.values():
            if auto_r(1 << (b - 1), m, 1 << 30) < 128:
                fail.append(f"uncapped rule gives < 128 at {b} bits")
    ident = [k for k, x in R["r32"].items() if k in mr and x["ops"] != mr[k]["ops"]]
    if ident:
        fail.append(f"identity control r32: {len(ident)} of {len(R['r32'])} rows differ from main")
    if fail:
        print("INVARIANT FAILURE:\n  " + "\n  ".join(fail))
        return 1

    rng = np.random.default_rng([SEED, 1])
    # per cell bootstrap replicates of log(sum arm / sum main), same resampled curves for both arms
    reps = {a: {} for a in TEST_ARMS}
    pts = {a: {} for a in TEST_ARMS}
    cells = {}
    for fam in FAMS:
        for b in SIZES:
            idx = rng.integers(0, n, size=(B, n))
            mm = np.array([mr[(fam, b, c, 0)]["ops"] for c in range(n)], float)
            cells[f"{fam}:{b}"] = {"curves": n, "main_S": float(np.mean([mr[(fam, b, c, 0)]["ops"] / math.sqrt(mr[(fam, b, c, 0)]["r"] / M[fam]) for c in range(n)]))}
            for a in TEST_ARMS:
                aa, _ = arrays(R[a], mr, fam, b, n)
                pts[a][(fam, b)] = math.log(aa.sum() / mm.sum())
                reps[a][(fam, b)] = np.log(aa[idx].sum(1) / mm[idx].sum(1))
                lo, hi = interval(reps[a][(fam, b)], 0.95)
                cells[f"{fam}:{b}"][a] = {"over_main": math.exp(pts[a][(fam, b)]), "ci95": [lo, hi]}
    out = {"seed": SEED, "bootstrap": B, "grid": n, "cells": cells, "sizes": {}, "arms": {}}
    L, Lrep = {}, {}
    for a in TEST_ARMS:
        L[a] = np.array([np.mean([pts[a][(f, b)] for f in FAMS]) for b in SIZES])
        Lrep[a] = np.stack([np.mean([reps[a][(f, b)] for f in FAMS], axis=0) for b in SIZES], axis=-1)   # (B, 5)
        for i, b in enumerate(SIZES):
            lo, hi = interval(Lrep[a][:, i], 0.95)
            out["sizes"][f"{a}:{b}"] = {"over_main": math.exp(L[a][i]), "ci95": [lo, hi]}
    robust = {}
    for a in TEST_ARMS:
        T, fit, slope = fit_T(L[a])
        T = int(T)
        Tb, _, _ = fit_T(Lrep[a])
        dist = {str(b): float((Tb == b).mean()) for b in SIZES}
        dist["none"] = float((Tb == -1).mean())
        arm = {"fit_over_main": [math.exp(float(v)) for v in fit], "slope_per_bit": float(slope), "T": T if T > 0 else None,
               "T_bootstrap_distribution": dist}
        if T > 0:
            ii = [i for i, b in enumerate(SIZES) if b >= T]
            S = float(L[a][ii].mean())
            Srep = Lrep[a][:, ii].mean(-1)
            ub = float(np.quantile(Srep, UB_COVER))
            worse = [SIZES[i] for i in ii if interval(Lrep[a][:, i], 0.95)[0] > 1]
            arm.update(suffix_sizes=[SIZES[i] for i in ii], suffix_geomean=math.exp(S), suffix_ub90=math.exp(ub),
                       suffix_ci95=interval(Srep, 0.95), sizes_wholly_worse=worse, robust=bool(ub < 0 and not worse))
            robust[a] = S if arm["robust"] else None
        else:
            arm["robust"] = False
        out["arms"][a] = arm
    cand = {a: S for a, S in robust.items() if S is not None}
    if not cand:
        out["rule"] = None
        out["verdict"] = "STOP: no arm passes the go gate; Phase 2 is not run"
    else:
        best = min(cand, key=cand.get)
        if len(cand) == 2 and abs(cand["r64"] - cand["r128"]) < TIE:
            best = "r64"
        C = int(best[1:])
        T = out["arms"][best]["T"]
        out["rule"] = {"arm": best, "cap_below_T": 32, "T": T, "cap_at_and_above_T": C}
        out["verdict"] = f"GO: cap = 32 for lg < {T}, cap = {C} for lg >= {T} (all larger sizes)"
    # controls
    ctl = {}
    for fam_key, (arm, grid) in {"r8": ("r8", POS)}.items():
        cs = []
        for fam in FAMS:
            for b, k in grid.items():
                cs.append(arrays(R[arm], mr, fam, b, min(k, n)))
        idxs = [rng.integers(0, len(a), size=(B, len(a))) for a, _ in cs]
        r = np.mean([np.log(a[i].sum(1) / m[i].sum(1)) for (a, m), i in zip(cs, idxs)], axis=0)
        pt = float(np.mean([math.log(a.sum() / m.sum()) for a, m in cs]))
        ci = interval(r, 0.95)
        ctl["positive_r8"] = {"over_main": math.exp(pt), "ci95": ci, "pass": ci[0] > 1}
    ctl["identity_r32"] = {"rows": len(R["r32"]), "differing": 0}
    out["controls"] = ctl
    (d / "results.json").write_text(json.dumps(out, indent=1) + "\n")

    f = lambda e: f"{e['over_main']:.3f} [{e['ci95'][0]:.3f}, {e['ci95'][1]:.3f}]"
    L_ = ["| size | both families r64/main | both families r128/main |", "|---|---|---|"]
    for b in SIZES:
        L_.append(f"| {b} | " + " | ".join(f(out["sizes"][f"{a}:{b}"]) for a in TEST_ARMS) + " |")
    L_ += ["", "| family | bits | curves | main S | r64/main | r128/main |", "|---|---|---|---|---|---|"]
    for k, c in cells.items():
        fam, bits = k.split(":")
        L_.append(f"| {fam} | {bits} | {c['curves']} | {c['main_S']:.3f} | " + " | ".join(f(c[a]) for a in TEST_ARMS) + " |")
    L_ += ["", "Intervals are 95% bootstrap intervals over curves (descriptive); S = group_ops / sqrt(n / m).", ""]
    for a in TEST_ARMS:
        r = out["arms"][a]
        L_.append(f"- {a}: fitted ratios by size {', '.join(f'{v:.4f}' for v in r['fit_over_main'])}; slope {r['slope_per_bit']:+.4f} per bit; T = {r['T']}; "
                  f"T over bootstrap draws {r['T_bootstrap_distribution']}")
        if r["T"]:
            L_.append(f"  - suffix {r['suffix_sizes']}: geomean {r['suffix_geomean']:.4f}, one-sided 90% upper bound {r['suffix_ub90']:.4f}, "
                      f"95% interval [{r['suffix_ci95'][0]:.4f}, {r['suffix_ci95'][1]:.4f}], sizes wholly worse {r['sizes_wholly_worse']}, robust {r['robust']}")
    L_ += ["", f"**Verdict: {out['verdict']}**", "",
           f"Positive control (table 8 vs main, 42 bits, both families, 95%): {f(ctl['positive_r8'])} pass={ctl['positive_r8']['pass']}",
           f"Identity control (forced 32 vs main): {ctl['identity_r32']['rows']} rows, all identical"]
    (d / "results.md").write_text("Ratios of curve_solve group operations to main (r = 32) on the same targets.\n\n" + "\n".join(L_) + "\n")
    print((d / "results.md").read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
