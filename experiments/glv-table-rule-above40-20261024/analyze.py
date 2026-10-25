#!/usr/bin/env python3
"""Analysis frozen with PROTOCOL.md. Reads rows_<arm>_<part>.jsonl.gz (parts p1, p2), checks the
invariants, writes results.json and results.md. Exits non-zero, writing nothing, if any invariant fails."""
from __future__ import annotations

import glob
import gzip
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = 20261031
TEST_ARMS = ["r64", "r128", "noesc"]          # decision arms, full grid
CTRL_ARMS = ["r8", "r32"]                      # controls, sizes 40 and 42 only
CTRL_SIZES = (40, 42)
SIZES = [40, 42, 44, 46, 48, 50]
GRID = {40: 800, 42: 650, 44: 450, 46: 300, 48: 170, 50: 85}   # curves per family; one target per curve
B = 10000
K = len(TEST_ARMS) * 2 * len(SIZES)            # 36 decision comparisons
ALPHA = 0.05 / K
M = {"j1728": 4, "j0": 6}


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


def per_curve(keys, A, Bm, field="ops", denom_field="ops"):
    per = defaultdict(lambda: [0, 0])
    for k in keys:
        per[k[2]][0] += A[k][field]
        per[k[2]][1] += Bm[k][denom_field]
    return list(per.values())


def ratio(v, idx):
    return sum(v[i][0] for i in idx) / sum(v[i][1] for i in idx)


def boot(v, rng, alphas):
    n = len(v)
    bs = sorted(ratio(v, [rng.randrange(n) for _ in range(n)]) for _ in range(B))
    q = lambda a: bs[min(B - 1, max(0, int(a * B)))]
    return ratio(v, range(n)), [(q(a / 2), q(1 - a / 2)) for a in alphas]


def main() -> int:
    R = {a: load(a) for a in ["main"] + TEST_ARMS + CTRL_ARMS}
    mr = R["main"]
    fail = []
    for a, rows in R.items():
        bad = [k for k, x in rows.items() if not x["correct"]]
        if bad:
            fail.append(f"{a}: {len(bad)} wrong answers")
    if any(not x.get("rho_correct", False) for x in mr.values()):
        fail.append("rho reference: wrong or missing answers")
    want = {(f, b, c, 0) for f in M for b in SIZES for c in range(GRID[b])}
    if set(mr) != want:
        fail.append("main: grid is not the frozen grid")
    for a in TEST_ARMS + CTRL_ARMS:
        w = want if a in TEST_ARMS else {k for k in want if k[1] in CTRL_SIZES}
        if set(R[a]) != w:
            fail.append(f"{a}: grid differs from the frozen grid")
        for k, x in R[a].items():
            m = mr.get(k)
            if m and (m["p"], m["a"], m["b"], m["k"]) != (x["p"], x["a"], x["b"], x["k"]):
                fail.append(f"{a}: different curve or target at {k}")
                break
    # main's own table choice at these sizes
    mains_r = {auto_r(x["r"], M[k[0]]) for k, x in mr.items()}
    if mains_r != {32}:
        fail.append(f"main's rule picks {sorted(mains_r)}, not only 32 (protocol assumes 32)")
    # identity control: forced 32 == main's own choice, so counts must be identical
    ident = [(k, x) for k, x in R["r32"].items() if x["ops"] != mr[k]["ops"]]
    if ident:
        fail.append(f"identity control r32: {len(ident)} of {len(R['r32'])} rows differ from main")
    # escape-off sanity: arms differ only in the build; row identity of curve/target already checked
    if fail:
        print("INVARIANT FAILURE:\n  " + "\n  ".join(fail))
        return 1

    out = {"seed": SEED, "comparisons": K, "alpha_each": ALPHA, "bootstrap": B,
           "identity_control_r32": {"rows": len(R["r32"]), "differing": 0}, "cells": {}, "controls": {}, "pooled": {}}
    for fam in M:
        for bits in SIZES:
            keys = [k for k in mr if k[0] == fam and k[1] == bits]
            m = M[fam]
            cell = {"main_table_r": 32, "targets": len(keys), "curves": len({k[2] for k in keys}),
                    "main_S": sum(mr[k]["ops"] / math.sqrt(mr[k]["r"] / m) for k in keys) / len(keys),
                    "rho_S": sum(mr[k]["rho_ops"] / math.sqrt(mr[k]["r"]) for k in keys) / len(keys),
                    "main_over_rho": sum(mr[k]["ops"] for k in keys) / sum(mr[k]["rho_ops"] for k in keys),
                    "arms": {}}
            for a in TEST_ARMS:
                v = per_curve(keys, R[a], mr)
                p, (ci, adj) = boot(v, random.Random(f"{SEED}:{a}:{fam}:{bits}"), [0.05, ALPHA])
                verdict = "fewer ops than main" if adj[1] < 1 else "more ops than main" if adj[0] > 1 else "not resolved"
                cell["arms"][a] = {"over_main": p, "ci95": ci, "ci_adjusted": adj, "verdict": verdict,
                                   "over_rho": sum(R[a][k]["ops"] for k in keys) / sum(mr[k]["rho_ops"] for k in keys)}
            out["cells"][f"{fam}:{bits}"] = cell
    # positive control: r8 vs main at 40 and 42 bits, pooled over both families and both sizes
    ck = [k for k in R["r8"]]
    v = per_curve(ck, R["r8"], mr)
    p, (ci,) = boot(v, random.Random(f"{SEED}:r8:pooled"), [0.05])
    out["controls"]["r8_vs_main_pooled_40_42"] = {"over_main": p, "ci95": ci, "pass": ci[0] > 1}
    for fam in M:
        for bits in CTRL_SIZES:
            keys = [k for k in R["r8"] if k[0] == fam and k[1] == bits]
            v = per_curve(keys, R["r8"], mr)
            p, (ci,) = boot(v, random.Random(f"{SEED}:r8:{fam}:{bits}"), [0.05])
            out["controls"][f"r8:{fam}:{bits}"] = {"over_main": p, "ci95": ci}
    # descriptive pooled summary over 42..50: geometric mean of the six... cell ratios per arm and family
    for a in TEST_ARMS:
        for fam in list(M) + ["both"]:
            fams = list(M) if fam == "both" else [fam]
            cells = [[per_curve([k for k in mr if k[0] == f and k[1] == b], R[a], mr) for b in SIZES if b > 40] for f in fams]
            cells = [c for cf in cells for c in cf]
            rng = random.Random(f"{SEED}:pool:{a}:{fam}")
            gm = lambda cs: math.exp(sum(math.log(ratio(c, range(len(c)))) for c in cs) / len(cs))
            bs = sorted(gm([[c[rng.randrange(len(c))] for _ in c] for c in cells]) for _ in range(2000))
            out["pooled"][f"{a}:{fam}"] = {"geomean_over_main_42_50": gm(cells), "ci95": (bs[50], bs[1949])}
    (HERE / "results.json").write_text(json.dumps(out, indent=1) + "\n")
    L = ["| family | bits | main S | rho S | main/rho | r64/main | r128/main | no-escape/main |", "|---|---|---|---|---|---|---|---|"]
    fmt = lambda e: f"{e['over_main']:.3f} [{e['ci_adjusted'][0]:.3f}, {e['ci_adjusted'][1]:.3f}]" + (" ✓" if e["verdict"].startswith("fewer") else " ✗" if e["verdict"].startswith("more") else "")
    for key, c in out["cells"].items():
        fam, bits = key.split(":")
        L.append(f"| {fam} | {bits} | {c['main_S']:.3f} | {c['rho_S']:.3f} | {c['main_over_rho']:.3f} | " + " | ".join(fmt(c["arms"][a]) for a in TEST_ARMS) + " |")
    L += ["", "Positive control (table 8 vs main, 40 and 42 bits, 95% intervals):", ""]
    L += [f"- {k}: {v['over_main']:.3f} [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}]" + (f" pass={v['pass']}" if "pass" in v else "") for k, v in out["controls"].items()]
    L += ["", "Descriptive pooled geometric mean of cell ratios, 42-50 bits (95%):", ""]
    L += [f"- {k}: {v['geomean_over_main_42_50']:.3f} [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}]" for k, v in out["pooled"].items()]
    (HERE / "results.md").write_text("Ratios of curve_solve group operations to main on the same targets; "
                                     f"intervals are {100 * (1 - ALPHA):.3f}% (Bonferroni over {K}); "
                                     "✓ fewer ops than main, ✗ more, unmarked not resolved.\n\n" + "\n".join(L) + "\n")
    print((HERE / "results.md").read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
