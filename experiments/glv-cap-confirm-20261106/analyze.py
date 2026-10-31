#!/usr/bin/env python3
"""Analysis frozen with PROTOCOL.md. Reads rows_<arm>_<part>.jsonl.gz (arms main, cand, mainid, candid; parts p1, p2) from
--dir (default: this directory), checks the invariants, writes results.json and results.md. Exits non-zero, writing nothing,
if any invariant fails."""
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
SEED = 20261106
SIZES = [40, 41, 42, 43]            # sizes where the candidate differs from main (cap 128 vs 32)
IDSIZES = [38, 39]                  # sizes where the candidate is main's rule: identity checks
FAMS = ["j1728", "j0"]
M = {"j1728": 4, "j0": 6}
N, NID, NRHO = 1600, 80, 60
B = 10000
COVER_PRIMARY = 0.975               # two-sided percentile interval; confirmed if the upper bound is below 1
COVER_SIZE = 1 - 0.05 / len(SIZES)  # no-worse check per size, Bonferroni over 4 sizes: 98.75%


def rule(n: int, m: int, cand: bool) -> int:
    """the table size glv_rho_solve picks: main cap 32; candidate cap 128 for bitlen(n) >= 40."""
    sqrt_nm = math.isqrt(n // m) + 1
    lg = n.bit_length()
    rbudget = sqrt_nm // (12 * lg)
    cap = 128 if (cand and lg >= 40) else 32
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


def hash_(s: str) -> int:
    return sum((i + 1) * ord(c) for i, c in enumerate(s))


def interval(reps, cover):
    lo, hi = np.quantile(reps, [(1 - cover) / 2, 1 - (1 - cover) / 2])
    return float(math.exp(lo)), float(math.exp(hi))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(HERE))
    ap.add_argument("--n", type=int, default=N)
    ap.add_argument("--nid", type=int, default=NID)
    ap.add_argument("--nrho", type=int, default=NRHO)
    a_ = ap.parse_args()
    d, n, nid, nrho = Path(a_.dir), a_.n, a_.nid, a_.nrho
    R = {a: load(d, a) for a in ["main", "cand", "mainid", "candid"]}
    mr, cr = R["main"], R["cand"]
    fail = []
    for a, rows in R.items():
        bad = [k for k, x in rows.items() if not x["correct"]]
        if bad:
            fail.append(f"{a}: {len(bad)} wrong answers")
    want = {(f, b, c, 0) for f in FAMS for b in SIZES for c in range(n)}
    wantid = {(f, b, c, 0) for f in FAMS for b in IDSIZES for c in range(nid)}
    for a, w in [("main", want), ("cand", want), ("mainid", wantid), ("candid", wantid)]:
        if set(R[a]) != w:
            fail.append(f"{a}: grid differs from the frozen grid")
    for a, ref in [("cand", "main"), ("candid", "mainid")]:
        for k, x in R[a].items():
            m = R[ref].get(k)
            if m and (m["p"], m["a"], m["b"], m["k"]) != (x["p"], x["a"], x["b"], x["k"]):
                fail.append(f"{a}: different curve or target at {k}")
                break
    wantr = {k for k in want if k[2] < nrho}
    got_rho = {k for k, x in mr.items() if "rho_ops" in x}
    if got_rho != wantr:
        fail.append("main: rho reference is not on exactly curves 0..NRHO-1 of every primary cell")
    if any(not mr[k].get("rho_correct", False) for k in got_rho):
        fail.append("rho reference: wrong answers")
    for rows, cand, name in [(mr, False, "main"), (R["mainid"], False, "mainid"), (R["candid"], True, "candid"), (cr, True, "cand")]:
        exp = {(rule(x["r"], M[k[0]], cand)) for k, x in rows.items() if k[1] in SIZES}
        if name in ("main", "mainid", "candid") and rows and any(rule(x["r"], M[k[0]], cand) != 32 for k, x in rows.items()):
            fail.append(f"{name}: rule does not pick 32 everywhere")
        if name == "cand" and exp != {128}:
            fail.append(f"cand: rule picks {sorted(exp)}, not only 128 at 40-43 bits")
    ident = [k for k, x in R["candid"].items() if x["ops"] != R["mainid"][k]["ops"]]
    if ident:
        fail.append(f"identity: {len(ident)} of {len(R['candid'])} rows at 38-39 bits differ between candidate and main")
    if fail:
        print("INVARIANT FAILURE:\n  " + "\n  ".join(fail))
        return 1

    def arr(f, b):
        return (np.array([cr[(f, b, c, 0)]["ops"] for c in range(n)], float),
                np.array([mr[(f, b, c, 0)]["ops"] for c in range(n)], float))

    out = {"seed": SEED, "bootstrap": B, "n": n, "identity": {"rows": len(R["candid"]), "differing": 0},
           "cells": {}, "by_size": {}, "by_family": {}}
    rng = np.random.default_rng([SEED, 1])
    cellrep, cellpt = {}, {}
    for f in FAMS:
        for b in SIZES:
            a, m = arr(f, b)
            idx = rng.integers(0, n, size=(B, n))
            cellpt[(f, b)] = math.log(a.sum() / m.sum())
            cellrep[(f, b)] = np.log(a[idx].sum(1) / m[idx].sum(1))
            rk = [(f, b, c, 0) for c in range(nrho)]
            rho_sum = sum(mr[k]["rho_ops"] for k in rk)
            out["cells"][f"{f}:{b}"] = {
                "curves": n, "over_main": math.exp(cellpt[(f, b)]), "ci95": interval(cellrep[(f, b)], 0.95),
                "main_S": float(np.mean([mr[(f, b, c, 0)]["ops"] / math.sqrt(mr[(f, b, c, 0)]["r"] / M[f]) for c in range(n)])),
                "cand_S": float(np.mean([cr[(f, b, c, 0)]["ops"] / math.sqrt(cr[(f, b, c, 0)]["r"] / M[f]) for c in range(n)])),
                "rho_S": float(np.mean([mr[k]["rho_ops"] / math.sqrt(mr[k]["r"]) for k in rk])),
                "main_over_rho": sum(mr[k]["ops"] for k in rk) / rho_sum, "cand_over_rho": sum(cr[k]["ops"] for k in rk) / rho_sum}
    keys = list(cellpt)
    pt = float(np.mean([cellpt[k] for k in keys]))
    reps = np.mean([cellrep[k] for k in keys], axis=0)
    lo, hi = interval(reps, COVER_PRIMARY)
    out["primary"] = {"geomean_over_main": math.exp(pt), "ci": [lo, hi], "coverage": COVER_PRIMARY,
                      "half_width": (hi - lo) / 2 / math.exp(pt), "ci95": interval(reps, 0.95), "confirmed": hi < 1}
    worse = []
    for b in SIZES:
        r = np.mean([cellrep[(f, b)] for f in FAMS], axis=0)
        p = float(np.mean([cellpt[(f, b)] for f in FAMS]))
        ci = interval(r, COVER_SIZE)
        out["by_size"][str(b)] = {"geomean_over_main": math.exp(p), "ci_bonferroni": ci, "ci95": interval(r, 0.95), "wholly_worse": ci[0] > 1}
        if ci[0] > 1:
            worse.append(b)
    out["no_worse"] = {"coverage": COVER_SIZE, "sizes_wholly_worse": worse, "pass": not worse}
    for f in FAMS:
        r = np.mean([cellrep[(f, b)] for b in SIZES], axis=0)
        p = float(np.mean([cellpt[(f, b)] for b in SIZES]))
        out["by_family"][f] = {"geomean_over_main": math.exp(p), "ci95": interval(r, 0.95)}
    out["verdict"] = ("CONFIRMED" if out["primary"]["confirmed"] and out["no_worse"]["pass"] else
                      "CONFIRMED_BUT_WORSE_AT_SOME_SIZE" if out["primary"]["confirmed"] else "NOT_CONFIRMED")
    (d / "results.json").write_text(json.dumps(out, indent=1) + "\n")

    L = ["| family | bits | curves | main S | cand S | rho S | cand/main | main/rho | cand/rho |", "|---|---|---|---|---|---|---|---|---|"]
    for k, c in out["cells"].items():
        fam, bits = k.split(":")
        L.append(f"| {fam} | {bits} | {c['curves']} | {c['main_S']:.3f} | {c['cand_S']:.3f} | {c['rho_S']:.3f} | "
                 f"{c['over_main']:.3f} [{c['ci95'][0]:.3f}, {c['ci95'][1]:.3f}] | {c['main_over_rho']:.3f} | {c['cand_over_rho']:.3f} |")
    p = out["primary"]
    L += ["", "Cell intervals are 95% bootstrap intervals (descriptive). S = group_ops / sqrt(n / m) for GLV, group_ops / sqrt(n) for rho; "
          f"rho on curves 0..{nrho - 1} of each cell (cand/rho and main/rho use the same curves).", "",
          f"Primary (8 cells, geometric mean of cell ratios, 97.5% interval): {p['geomean_over_main']:.4f} [{p['ci'][0]:.4f}, {p['ci'][1]:.4f}], "
          f"half-width {100 * p['half_width']:.2f}%, 95% interval [{p['ci95'][0]:.4f}, {p['ci95'][1]:.4f}], "
          f"{'CONFIRMED (upper bound below 1)' if p['confirmed'] else 'not confirmed'}", "",
          f"No-worse check per size (both families, {100 * COVER_SIZE:.2f}% intervals; fails if a lower bound is above 1): pass={out['no_worse']['pass']}", ""]
    L += [f"- {b} bits: {v['geomean_over_main']:.4f} [{v['ci_bonferroni'][0]:.4f}, {v['ci_bonferroni'][1]:.4f}] (95%: [{v['ci95'][0]:.4f}, {v['ci95'][1]:.4f}])"
          for b, v in out["by_size"].items()]
    L += ["", "Per family (sizes 40-43 pooled, 95%, descriptive):", ""]
    L += [f"- {f}: {v['geomean_over_main']:.4f} [{v['ci95'][0]:.4f}, {v['ci95'][1]:.4f}]" for f, v in out["by_family"].items()]
    L += ["", f"Identity cells (38 and 39 bits, {len(R['candid'])} rows): candidate group_ops equal main's on every row.", "", f"**Verdict: {out['verdict']}**"]
    (d / "results.md").write_text("Ratios of curve_solve group operations, candidate over main, on the same targets.\n\n" + "\n".join(L) + "\n")
    print((d / "results.md").read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
