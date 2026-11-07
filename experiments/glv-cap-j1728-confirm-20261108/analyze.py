#!/usr/bin/env python3
"""Analysis frozen with PROTOCOL.md. Reads rows_<arm>_<part>.jsonl.gz from --dir, checks the invariants, writes results.json
and results.md. Exits non-zero, writing nothing, if any invariant fails. Arms: ref (1ee4f47, cap 32), cand (candidate), main
(318b27bf, cap 128 from 40 bits for both families; arms mainid, mainj0), refid / candid (identity cells), r8 (positive control),
candj0 (candidate on the j = 0 secondary cells)."""
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
SEED = 20261108
SIZES = [40, 41, 42, 43]
M = {"j1728": 4, "j0": 6}
N, NJ0, NID, NRHO, NRHO0, NCTRL = 3000, 800, 100, 60, 40, 200
B = 10000
COVER_PRIMARY = 0.975                     # K = 2: two-sided 97.5%, confirmed if the upper bound is below 1
COVER_SIZE = 1 - 0.05 / len(SIZES)        # Bonferroni over 4 sizes: 98.75%


def rule(n: int, m: int, arm: str) -> int:
    """the table size glv_rho_solve picks. ref: cap 32. main: cap 128 from 40 bits (both families). cand: cap 128 from 40 bits when m == 4."""
    sqrt_nm = math.isqrt(n // m) + 1
    lg = n.bit_length()
    rbudget = sqrt_nm // (12 * lg)
    cap = 128 if (lg >= 40 and (arm == "main" or (arm == "cand" and m == 4))) else 32
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


def interval(reps, cover):
    lo, hi = np.quantile(reps, [(1 - cover) / 2, 1 - (1 - cover) / 2])
    return float(math.exp(lo)), float(math.exp(hi))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(HERE))
    ap.add_argument("--n", type=int, default=N)
    ap.add_argument("--nj0", type=int, default=NJ0)
    ap.add_argument("--nid", type=int, default=NID)
    ap.add_argument("--nctrl", type=int, default=NCTRL)
    ap.add_argument("--nrho", type=int, default=NRHO)
    ap.add_argument("--nrho0", type=int, default=NRHO0)
    a_ = ap.parse_args()
    d, n, nj0, nid, nctrl = Path(a_.dir), a_.n, a_.nj0, a_.nid, a_.nctrl
    NRHO_, NRHO0_ = a_.nrho, a_.nrho0
    arms = ["ref", "cand", "refid", "candid", "mainid", "r8", "candj0", "mainj0"]
    R = {a: load(d, a) for a in arms}
    fail = []
    for a, rows in R.items():
        bad = [k for k, x in rows.items() if not x["correct"]]
        if bad:
            fail.append(f"{a}: {len(bad)} wrong answers")
    g = lambda fam, sizes, k: {(fam, b, c, 0) for b in sizes for c in range(k)}
    want = {"ref": g("j1728", SIZES, n), "cand": g("j1728", SIZES, n),
            "refid": g("j0", SIZES, nid) | g("j1728", [38, 39], nid), "candid": g("j0", SIZES, nid) | g("j1728", [38, 39], nid),
            "mainid": g("j1728", SIZES, nid), "r8": g("j1728", [42], nctrl),
            "candj0": g("j0", SIZES, nj0), "mainj0": g("j0", SIZES, nj0)}
    for a, w in want.items():
        if set(R[a]) != w:
            fail.append(f"{a}: grid differs from the frozen grid")
    same = lambda x, y: (x["p"], x["a"], x["b"], x["k"]) == (y["p"], y["a"], y["b"], y["k"])
    for a, ref in [("cand", "ref"), ("refid", "candid"), ("mainid", "cand"), ("r8", "ref"), ("candj0", "mainj0")]:
        for k, x in R[a].items():
            y = R[ref].get(k)
            if y is not None and not same(x, y):
                fail.append(f"{a}: different curve or target than {ref} at {k}")
                break
    # rule coverage: which table sizes each arm is expected to use (recomputed from n), recorded for the report
    exp = {}
    for a, arm in [("ref", "ref"), ("cand", "cand"), ("candj0", "cand"), ("mainj0", "main"), ("mainid", "main")]:
        exp[a] = sorted({rule(x["r"], M[k[0]], arm) for k, x in R[a].items()})
    if exp["ref"] != [32] or exp["candj0"] != [32] or exp["cand"] != [128] or exp["mainj0"] != [128] or exp["mainid"] != [128]:
        fail.append(f"selector rule not as frozen: {exp}")
    ident = [k for k, x in R["candid"].items() if x["ops"] != R["refid"][k]["ops"]]
    if ident:
        fail.append(f"identity: {len(ident)} of {len(R['candid'])} rows differ between candidate and ref (j0 at 40-43, j1728 at 38-39)")
    identm = [k for k, x in R["mainid"].items() if x["ops"] != R["cand"][k]["ops"]]
    if identm:
        fail.append(f"identity: {len(identm)} of {len(R['mainid'])} j1728 rows at 40-43 differ between candidate and current main")
    rho_ok = lambda rows, fam, k: {key for key, x in rows.items() if "rho_ops" in x} == g(fam, SIZES, k)
    if not rho_ok(R["ref"], "j1728", NRHO_) or not rho_ok(R["mainj0"], "j0", NRHO0_):
        fail.append("rho reference is not on exactly the frozen curves")
    if any(not x.get("rho_correct", False) for a in ("ref", "mainj0") for x in R[a].values() if "rho_ops" in x):
        fail.append("rho reference: wrong answers")
    if fail:
        print("INVARIANT FAILURE:\n  " + "\n  ".join(fail))
        return 1

    rng = np.random.default_rng([SEED, 1])
    out = {"seed": SEED, "bootstrap": B, "n": n, "nj0": nj0, "rule_tables": exp,
           "identity": {"cand_vs_ref_rows": len(R["candid"]), "cand_vs_ref_differing": 0,
                        "cand_vs_main_j1728_rows": len(R["mainid"]), "cand_vs_main_j1728_differing": 0},
           "cells": {}, "by_size": {}, "s2": {"cells": {}, "by_size": {}}}

    def pair(A, Bm, fam, b, k):
        a = np.array([A[(fam, b, c, 0)]["ops"] for c in range(k)], float)
        m = np.array([Bm[(fam, b, c, 0)]["ops"] for c in range(k)], float)
        idx = rng.integers(0, k, size=(B, k))
        return math.log(a.sum() / m.sum()), np.log(a[idx].sum(1) / m[idx].sum(1))

    S = lambda x, f: x["ops"] / math.sqrt(x["r"] / M[f])
    cellpt, cellrep = {}, {}
    for b in SIZES:
        pt, rep = pair(R["cand"], R["ref"], "j1728", b, n)
        cellpt[b], cellrep[b] = pt, rep
        rk = [("j1728", b, c, 0) for c in range(NRHO_)]
        rho = sum(R["ref"][k]["rho_ops"] for k in rk)
        out["cells"][str(b)] = {
            "curves": n, "cand_over_ref": math.exp(pt), "ci95": interval(rep, 0.95), "ci_bonferroni": interval(rep, COVER_SIZE),
            "wholly_worse": interval(rep, COVER_SIZE)[0] > 1, "wholly_better": interval(rep, COVER_SIZE)[1] < 1,
            "ref_S": float(np.mean([S(R["ref"][("j1728", b, c, 0)], "j1728") for c in range(n)])),
            "cand_S": float(np.mean([S(R["cand"][("j1728", b, c, 0)], "j1728") for c in range(n)])),
            "rho_S": float(np.mean([R["ref"][k]["rho_ops"] / math.sqrt(R["ref"][k]["r"]) for k in rk])),
            "ref_over_rho": sum(R["ref"][k]["ops"] for k in rk) / rho, "cand_over_rho": sum(R["cand"][k]["ops"] for k in rk) / rho}
    pt = float(np.mean(list(cellpt.values())))
    reps = np.mean([cellrep[b] for b in SIZES], axis=0)
    lo, hi = interval(reps, COVER_PRIMARY)
    out["primary"] = {"geomean_cand_over_ref": math.exp(pt), "ci": [lo, hi], "coverage": COVER_PRIMARY,
                      "half_width": (hi - lo) / 2 / math.exp(pt), "ci95": interval(reps, 0.95), "confirmed": hi < 1}
    worse = [b for b in SIZES if out["cells"][str(b)]["wholly_worse"]]
    out["no_worse"] = {"coverage": COVER_SIZE, "sizes_wholly_worse": worse, "pass": not worse}

    # S2: j = 0, candidate (cap 32) over current main (cap 128); the candidate's j = 0 path is the ref's (identity cells)
    pts2, reps2 = {}, {}
    for b in SIZES:
        pt2, rep2 = pair(R["candj0"], R["mainj0"], "j0", b, nj0)
        pts2[b], reps2[b] = pt2, rep2
        rk = [("j0", b, c, 0) for c in range(NRHO0_)]
        rho = sum(R["mainj0"][k]["rho_ops"] for k in rk)
        out["s2"]["cells"][str(b)] = {
            "curves": nj0, "cand_over_main": math.exp(pt2), "ci95": interval(rep2, 0.95), "ci_bonferroni": interval(rep2, COVER_SIZE),
            "main_S": float(np.mean([S(R["mainj0"][("j0", b, c, 0)], "j0") for c in range(nj0)])),
            "cand_S": float(np.mean([S(R["candj0"][("j0", b, c, 0)], "j0") for c in range(nj0)])),
            "rho_S": float(np.mean([R["mainj0"][k]["rho_ops"] / math.sqrt(R["mainj0"][k]["r"]) for k in rk])),
            "main_over_rho": sum(R["mainj0"][k]["ops"] for k in rk) / rho, "cand_over_rho": sum(R["candj0"][k]["ops"] for k in rk) / rho}
    p2 = float(np.mean(list(pts2.values())))
    r2 = np.mean([reps2[b] for b in SIZES], axis=0)
    l2, h2 = interval(r2, COVER_PRIMARY)
    out["s2"]["pooled"] = {"geomean_cand_over_main": math.exp(p2), "ci": [l2, h2], "coverage": COVER_PRIMARY, "ci95": interval(r2, 0.95)}

    # positive control
    pt3, rep3 = pair(R["r8"], R["ref"], "j1728", 42, nctrl)
    ci3 = interval(rep3, 0.95)
    out["control"] = {"r8_over_ref_42bits": math.exp(pt3), "ci95": ci3, "pass": ci3[0] > 1, "curves": nctrl}

    out["verdict"] = ("CONFIRMED" if out["primary"]["confirmed"] and out["no_worse"]["pass"] else
                      "CONFIRMED_BUT_WORSE_AT_SOME_SIZE" if out["primary"]["confirmed"] else "NOT_CONFIRMED")
    (d / "results.json").write_text(json.dumps(out, indent=1) + "\n")

    L = ["Primary and secondary S1: j = 1728, candidate over ref (1ee4f47, cap 32 everywhere), ratio of curve_solve group operations on the same targets.", "",
         "| bits | curves | ref S | cand S | rho S | cand/ref (95%) | cand/ref (98.75%) | ref/rho | cand/rho |", "|---|---|---|---|---|---|---|---|---|"]
    for b, c in out["cells"].items():
        L.append(f"| {b} | {c['curves']} | {c['ref_S']:.3f} | {c['cand_S']:.3f} | {c['rho_S']:.3f} | {c['cand_over_ref']:.4f} [{c['ci95'][0]:.4f}, {c['ci95'][1]:.4f}] | "
                 f"[{c['ci_bonferroni'][0]:.4f}, {c['ci_bonferroni'][1]:.4f}] | {c['ref_over_rho']:.3f} | {c['cand_over_rho']:.3f} |")
    p = out["primary"]
    L += ["", f"S = group_ops / sqrt(n / m) for GLV, group_ops / sqrt(n) for rho (rho on curves 0..{NRHO_ - 1} of each cell; the /rho columns use the same curves).", "",
          f"**Primary** (j = 1728, 40-43 bits, geometric mean of the 4 cell ratios, 97.5% interval): {p['geomean_cand_over_ref']:.4f} [{p['ci'][0]:.4f}, {p['ci'][1]:.4f}], "
          f"half-width {100 * p['half_width']:.2f}%, 95% interval [{p['ci95'][0]:.4f}, {p['ci95'][1]:.4f}], {'CONFIRMED (upper bound below 1)' if p['confirmed'] else 'NOT confirmed'}", "",
          f"No-worse check ({100 * COVER_SIZE:.2f}% per-size intervals; fails if a lower bound is above 1): pass={out['no_worse']['pass']}; sizes wholly better: "
          f"{[int(b) for b, c in out['cells'].items() if c['wholly_better']]}", "",
          "Secondary S2: j = 0, candidate (cap 32) over current main (318b27bf, cap 128 from 40 bits), same targets.", "",
          "| bits | curves | main S | cand S | rho S | cand/main (95%) | cand/main (98.75%) | main/rho | cand/rho |", "|---|---|---|---|---|---|---|---|---|"]
    for b, c in out["s2"]["cells"].items():
        L.append(f"| {b} | {c['curves']} | {c['main_S']:.3f} | {c['cand_S']:.3f} | {c['rho_S']:.3f} | {c['cand_over_main']:.4f} [{c['ci95'][0]:.4f}, {c['ci95'][1]:.4f}] | "
                 f"[{c['ci_bonferroni'][0]:.4f}, {c['ci_bonferroni'][1]:.4f}] | {c['main_over_rho']:.3f} | {c['cand_over_rho']:.3f} |")
    q = out["s2"]["pooled"]
    L += ["", f"S2 pooled (j = 0, 40-43 bits, 97.5%): {q['geomean_cand_over_main']:.4f} [{q['ci'][0]:.4f}, {q['ci'][1]:.4f}] (95%: [{q['ci95'][0]:.4f}, {q['ci95'][1]:.4f}]); rho on curves 0..{NRHO0_ - 1}.", "",
          f"Identity (exact): candidate equals ref on all {len(R['candid'])} rows (j = 0 at 40-43, j = 1728 at 38-39); candidate equals current main on all {len(R['mainid'])} j = 1728 rows at 40-43 (first {nid} curves per size).", "",
          f"Positive control (forced r = 8 over ref, j = 1728, 42 bits, {nctrl} curves): {out['control']['r8_over_ref_42bits']:.3f} [{ci3[0]:.3f}, {ci3[1]:.3f}], {'detector sees it' if out['control']['pass'] else 'DETECTOR DID NOT SEE IT'}", "",
          f"**Verdict: {out['verdict']}**"]
    (d / "results.md").write_text("\n".join(L) + "\n")
    print((d / "results.md").read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
