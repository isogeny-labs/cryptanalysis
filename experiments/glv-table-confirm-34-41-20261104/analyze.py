#!/usr/bin/env python3
"""Analysis frozen with PROTOCOL.md. Reads rows_<arm>_<part>.jsonl.gz (parts p1, p2) from this directory,
checks the invariants, writes results.json and results.md. Exits non-zero, writing nothing, if any invariant fails."""
from __future__ import annotations

import glob
import gzip
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SEED = 20261104
PRIMARY_SIZES = [34, 36, 38, 40]
N_PRIMARY = 4000                               # curves per family per primary size; one target per curve
N_DESC = 1000                                  # curves per family at 32 bits (descriptive only)
CTRL_ID = 100                                  # identity control: capid on curves 0..99 of every cell
CTRL_R8 = 300                                  # positive control: r8 on curves 0..299 of the 34- and 40-bit cells
RHO_N = 150                                    # rho reference on main for curves 0..149 of every cell
FAMS = ["j1728", "j0"]
M = {"j1728": 4, "j0": 6}
B = 10000
COV_PRIMARY = 0.95                             # K = 1
K_SECONDARY = 4                                # 2 families + 2 size halves
COV_SECONDARY = 1 - 0.05 / K_SECONDARY         # 98.75%
HALVES = {"34-36": [34, 36], "38-40": [38, 40]}
if os.environ.get("A6_DRY"):  # end-to-end test on a tiny grid (dry run, not data); never set for the frozen run
    N_PRIMARY, N_DESC, CTRL_ID, CTRL_R8, RHO_N = 12, 6, 4, 8, 3
GRID = {(f, b): (N_PRIMARY if b in PRIMARY_SIZES else N_DESC) for f in FAMS for b in [32] + PRIMARY_SIZES}


def rule(n: int, m: int, cap: int) -> int:
    """glv_rho_solve's table rule: rbudget = (isqrt(n / m) + 1) / (12 * bitlen(n)), r doubles from 8 while 2r <= rbudget and 2r <= cap."""
    rb = (math.isqrt(n // m) + 1) // (12 * n.bit_length())
    r = 8
    while r * 2 <= rb and r * 2 <= cap:
        r *= 2
    return r


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


def arrays(A, Mr, fam, bits, n):
    a = np.array([A[(fam, bits, c, 0)]["ops"] for c in range(n)], float)
    m = np.array([Mr[(fam, bits, c, 0)]["ops"] for c in range(n)], float)
    return a, m


def boot_cell(a, m, rng):
    """point log(sum a / sum m) and B bootstrap replicates, curves resampled with replacement."""
    n = len(a)
    idx = rng.integers(0, n, size=(B, n))
    return math.log(a.sum() / m.sum()), np.log(a[idx].sum(axis=1) / m[idx].sum(axis=1))


def interval(reps, cover):
    lo, hi = np.quantile(reps, [(1 - cover) / 2, 1 - (1 - cover) / 2])
    return float(math.exp(lo)), float(math.exp(hi))


def pooled(cellboots, keys):
    pt = float(np.mean([cellboots[k][0] for k in keys]))
    reps = np.mean([cellboots[k][1] for k in keys], axis=0)
    return pt, reps


def summary(pt, reps, cover):
    lo, hi = interval(reps, cover)
    return {"geomean_over_main": math.exp(pt), "ci": [lo, hi], "coverage": cover,
            "half_width": (hi - lo) / 2 / math.exp(pt), "upper_below_1": hi < 1, "lower_above_1": lo > 1}


def main() -> int:
    R = {a: load(a) for a in ["main", "cand", "capid", "r8"]}
    mr, cr = R["main"], R["cand"]
    fail = []
    for a, rows in R.items():
        bad = [k for k, x in rows.items() if not x["correct"]]
        if bad:
            fail.append(f"{a}: {len(bad)} wrong answers")
    want = {(f, b, c, 0) for (f, b), n in GRID.items() for c in range(n)}
    for a in ("main", "cand"):
        if set(R[a]) != want:
            fail.append(f"{a}: grid is not the frozen grid")
    wantr = {k for k in want if k[2] < RHO_N}
    got_rho = {k for k, x in mr.items() if "rho_ops" in x}
    if got_rho != wantr:
        fail.append("main: rho reference is not on exactly curves 0..RHO_N-1 of every cell")
    if any(not mr[k].get("rho_correct", False) for k in got_rho):
        fail.append("rho reference: wrong answers")
    wants = {"capid": {k for k in want if k[2] < CTRL_ID},
             "r8": {k for k in want if k[1] in (34, 40) and k[2] < CTRL_R8}}
    for a in ("cand", "capid", "r8"):
        if set(R[a]) != (want if a == "cand" else wants[a]):
            fail.append(f"{a}: grid differs from the frozen grid")
        for k, x in R[a].items():
            m = mr.get(k)
            if m and (m["p"], m["a"], m["b"], m["k"], m["r"]) != (x["p"], x["a"], x["b"], x["k"], x["r"]):
                fail.append(f"{a}: different curve or target at {k}")
                break
    ident = [k for k, x in R["capid"].items() if x["ops"] != mr[k]["ops"]]
    if ident:
        fail.append(f"identity control: {len(ident)} of {len(R['capid'])} rows differ from main")
    # rows where the cap-128 and cap-32 rules choose the same table run the same code path and seeds: identical rows
    same = [k for k, x in mr.items() if rule(x["r"], M[k[0]], 32) == rule(x["r"], M[k[0]], 128)]
    samebad = [k for k in same if cr[k]["ops"] != mr[k]["ops"]]
    if samebad:
        fail.append(f"{len(samebad)} of {len(same)} rows with equal r under both rules differ between cand and main")
    if fail:
        print("INVARIANT FAILURE:\n  " + "\n  ".join(fail))
        return 1

    out = {"seed": SEED, "bootstrap": B, "grid": {f"{f}:{b}": n for (f, b), n in GRID.items()},
           "identity_control": {"rows": len(R["capid"]), "differing": 0},
           "equal_r_rows": {"rows": len(same), "differing": 0},
           "r_chosen": {}, "cells": {}, "primary": None, "secondary": {}, "by_size": {}, "positive_control": {}}
    boots, descr = {}, {}
    for fam in FAMS:
        for b in [32] + PRIMARY_SIZES:
            n = GRID[(fam, b)]
            keys = [(fam, b, c, 0) for c in range(n)]
            rk = [(fam, b, c, 0) for c in range(RHO_N)]
            r32 = [rule(mr[k]["r"], M[fam], 32) for k in keys]
            r128 = [rule(mr[k]["r"], M[fam], 128) for k in keys]
            out["r_chosen"][f"{fam}:{b}"] = {"main": {str(v): r32.count(v) for v in sorted(set(r32))},
                                              "cand": {str(v): r128.count(v) for v in sorted(set(r128))}}
            a, m = arrays(cr, mr, fam, b, n)
            rng = np.random.default_rng([SEED, M[fam], b])
            pt, reps = boot_cell(a, m, rng)
            boots[(fam, b)] = (pt, reps)
            out["cells"][f"{fam}:{b}"] = {
                "curves": n, "main_S": float(np.mean([mr[k]["ops"] / math.sqrt(mr[k]["r"] / M[fam]) for k in keys])),
                "cand_S": float(np.mean([cr[k]["ops"] / math.sqrt(cr[k]["r"] / M[fam]) for k in keys])),
                "rho_S": float(np.mean([mr[k]["rho_ops"] / math.sqrt(mr[k]["r"]) for k in rk])),
                "main_over_rho": sum(mr[k]["ops"] for k in rk) / sum(mr[k]["rho_ops"] for k in rk),
                "cand_over_rho": sum(cr[k]["ops"] for k in rk) / sum(mr[k]["rho_ops"] for k in rk),
                "cand_over_main": math.exp(pt), "ci95": interval(reps, 0.95),
                # per-target variance of log(cand/main), delta method (CV^2 of each arm), for the post-hoc power check
                "var_log_ratio": float((np.std(a) / np.mean(a)) ** 2 + (np.std(m) / np.mean(m)) ** 2)}
    pkeys = [(f, b) for f in FAMS for b in PRIMARY_SIZES]
    pt, reps = pooled(boots, pkeys)
    out["primary"] = summary(pt, reps, COV_PRIMARY)
    out["primary"]["confirmed"] = out["primary"]["upper_below_1"]
    out["primary"]["worse"] = out["primary"]["lower_above_1"]
    sec = {}
    for fam in FAMS:
        sec[f"family:{fam}"] = pooled(boots, [(fam, b) for b in PRIMARY_SIZES])
    for name, sizes in HALVES.items():
        sec[f"sizes:{name}"] = pooled(boots, [(f, b) for f in FAMS for b in sizes])
    for k, (pt_, reps_) in sec.items():
        out["secondary"][k] = summary(pt_, reps_, COV_SECONDARY)
    # descriptive: low half over high half, 95%
    d = sec["sizes:34-36"][1] - sec["sizes:38-40"][1]
    dpt = sec["sizes:34-36"][0] - sec["sizes:38-40"][0]
    out["halves_difference"] = {"ratio_low_over_high": math.exp(dpt), "ci95": interval(d, 0.95)}
    for b in PRIMARY_SIZES:
        pt_, reps_ = pooled(boots, [(f, b) for f in FAMS])
        out["by_size"][str(b)] = {"geomean_over_main": math.exp(pt_), "ci95": interval(reps_, 0.95)}
    pt_, reps_ = pooled(boots, [(f, 32) for f in FAMS])
    out["by_size"]["32"] = {"geomean_over_main": math.exp(pt_), "ci95": interval(reps_, 0.95)}
    # positive control: r8 vs main, 40 bits curves 0..299, both families (geometric mean of the two ratios of sums); 34 bits descriptive
    for b, key in ((40, "r8_over_main_40"), (34, "r8_over_main_34_descriptive")):
        bs = {}
        for fam in FAMS:
            bs[fam] = boot_cell(*arrays(R["r8"], mr, fam, b, CTRL_R8), np.random.default_rng([SEED, 8, M[fam], b]))
        pt_, reps_ = pooled(bs, FAMS)
        ci = interval(reps_, 0.95)
        out["positive_control"][key] = {"ratio": math.exp(pt_), "ci95": ci, "pass": ci[0] > 1}
    (HERE / "results.json").write_text(json.dumps(out, indent=1) + "\n")

    f3 = lambda x: f"{x:.3f}"
    L = ["| family | bits | curves | r (main -> cand) | main S | cand S | rho S | main/rho | cand/rho | cand/main (95%) |", "|---|---|---|---|---|---|---|---|---|---|"]
    for key, c in out["cells"].items():
        fam, bits = key.split(":")
        rc = out["r_chosen"][key]
        rtxt = "; ".join(f"{k}:{v}" for k, v in rc["main"].items()) + " -> " + "; ".join(f"{k}:{v}" for k, v in rc["cand"].items())
        L.append(f"| {fam} | {bits} | {c['curves']} | {rtxt} | {f3(c['main_S'])} | {f3(c['cand_S'])} | {f3(c['rho_S'])} | "
                 f"{f3(c['main_over_rho'])} | {f3(c['cand_over_rho'])} | {c['cand_over_main']:.3f} [{c['ci95'][0]:.3f}, {c['ci95'][1]:.3f}] |")
    p = out["primary"]
    L += ["", "Cell intervals are 95% bootstrap intervals, descriptive. S, main/rho and cand/rho use curves 0..149 of each cell for rho; "
          "the r column counts curves per table size under each rule.", "",
          f"Primary (both families, 8 cells at 34-40 bits, geometric mean of cell ratios, 95% interval, K = 1): "
          f"{p['geomean_over_main']:.4f} [{p['ci'][0]:.4f}, {p['ci'][1]:.4f}], half-width {100 * p['half_width']:.2f}%, "
          f"{'CONFIRMED (upper bound below 1)' if p['confirmed'] else ('WORSE (lower bound above 1)' if p['worse'] else 'not confirmed')}",
          "", f"Secondary ({100 * COV_SECONDARY:.2f}% interval, K = {K_SECONDARY}):", ""]
    L += [f"- {k}: {v['geomean_over_main']:.4f} [{v['ci'][0]:.4f}, {v['ci'][1]:.4f}], half-width {100 * v['half_width']:.2f}%, "
          f"{'upper bound below 1' if v['upper_below_1'] else ('lower bound above 1' if v['lower_above_1'] else 'interval contains 1')}"
          for k, v in out["secondary"].items()]
    h = out["halves_difference"]
    L += ["", f"Descriptive: 34-36 over 38-40 {h['ratio_low_over_high']:.4f} [{h['ci95'][0]:.4f}, {h['ci95'][1]:.4f}] (95%)", "",
          "Descriptive per size (both families, 95%):", ""]
    L += [f"- {k} bits: {v['geomean_over_main']:.4f} [{v['ci95'][0]:.4f}, {v['ci95'][1]:.4f}]" for k, v in out["by_size"].items()]
    L += ["", f"Identity control (cand with cap 32 vs main): {out['identity_control']['rows']} rows, 0 differing. "
          f"Rows with equal r under both rules: {out['equal_r_rows']['rows']}, 0 differing."]
    for k, v in out["positive_control"].items():
        L.append(f"Positive control {k}: {v['ratio']:.3f} [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}] pass={v['pass']}")
    (HERE / "results.md").write_text("Ratios of curve_solve group operations to main on the same targets.\n\n" + "\n".join(L) + "\n")
    print((HERE / "results.md").read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
