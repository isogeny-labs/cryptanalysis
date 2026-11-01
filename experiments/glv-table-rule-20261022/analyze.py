#!/usr/bin/env python3
"""Analysis frozen with PROTOCOL.md. Reads rows_<arm>.jsonl.gz, checks the
invariants, and writes results.json and results.md. Exits non-zero, writing
nothing, if any invariant fails."""
from __future__ import annotations

import gzip
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARMS = ["main", "r16", "r32", "r64", "cov"]
FORCED = {"r16": 16, "r32": 32, "r64": 64}
B = 10000
K = 3 * 2 * 8 + 8          # comparisons: 3 forced tables x 2 families x 8 sizes, + cov on j0 x 8 sizes
ALPHA = 0.05 / K


def auto_r(n: int, m: int) -> int:
    """main's table rule (src/curve.c, glv_rho_solve)."""
    sqrt_nm = math.isqrt(n // m) + 1
    lg = n.bit_length()                  # glv_ilog2(n) + 1
    rbudget = sqrt_nm // (48 * lg)
    rr = 8
    while rr * 2 <= rbudget and rr * 2 <= 32:
        rr *= 2
    return rr


def load(arm):
    rows = {}
    for line in gzip.open(HERE / f"rows_{arm}.jsonl.gz", "rt"):
        x = json.loads(line)
        key = (x["family"], x["bits"], x["curve"], x["target"])
        if key in rows:
            sys.exit(f"duplicate row {arm} {key}")
        rows[key] = x
    return rows


def ratio_ci(per_curve, rng):
    v = list(per_curve.values())
    st = lambda idx: sum(v[i][0] for i in idx) / sum(v[i][1] for i in idx)
    boots = sorted(st([rng.randrange(len(v)) for _ in v]) for _ in range(B))
    q = lambda a: boots[min(B - 1, max(0, int(a * B)))]
    return st(range(len(v))), (q(0.025), q(0.975)), (q(ALPHA / 2), q(1 - ALPHA / 2))


def main() -> int:
    R = {a: load(a) for a in ARMS}
    fail = []
    for a, rows in R.items():
        bad = [k for k, x in rows.items() if not x["correct"]]
        if bad:
            fail.append(f"{a}: {len(bad)} wrong answers")
    main_rows = R["main"]
    if any(not x.get("rho_correct", False) for x in main_rows.values()):
        fail.append("rho reference: wrong or missing answers")
    for a in ARMS[1:]:
        want = {k for k in main_rows if a != "cov" or k[0] == "j0"}
        if set(R[a]) != want:
            fail.append(f"{a}: grid differs from main")
        for k, x in R[a].items():
            m = main_rows.get(k)
            if m and (m["p"], m["a"], m["b"], m["k"]) != (x["p"], x["a"], x["b"], x["k"]):
                fail.append(f"{a}: different curve or target at {k}")
                break
    # identity control: a forced table equal to main's own choice must give identical counts
    ident = defaultdict(lambda: [0, 0])
    for a, rr in FORCED.items():
        for k, x in R[a].items():
            m = main_rows[k]
            if auto_r(m["r"], 4 if k[0] == "j1728" else 6) == rr:
                ident[a][0] += 1
                if x["ops"] != m["ops"]:
                    ident[a][1] += 1
    for a, (n, bad) in ident.items():
        if bad:
            fail.append(f"identity control {a}: {bad} of {n} differ from main")
    if fail:
        print("INVARIANT FAILURE:\n  " + "\n  ".join(fail))
        return 1

    out = {"alpha_family": 0.05, "comparisons": K, "alpha_each": ALPHA, "bootstrap": B,
           "identity_control": {a: {"rows_with_equal_table": n, "differing": bad} for a, (n, bad) in ident.items()},
           "cells": {}}
    for fam in ("j1728", "j0"):
        for bits in sorted({k[1] for k in main_rows}):
            keys = [k for k in main_rows if k[0] == fam and k[1] == bits]
            m = 4 if fam == "j1728" else 6
            cell = {"main_table_r": sorted({auto_r(main_rows[k]["r"], m) for k in keys}),
                    "targets": len(keys), "curves": len({k[2] for k in keys}),
                    "main_over_rho": sum(main_rows[k]["ops"] for k in keys) / sum(main_rows[k]["rho_ops"] for k in keys),
                    "arms": {}}
            for a in ARMS[1:]:
                if a == "cov" and fam != "j0":
                    continue
                per = defaultdict(lambda: [0, 0])
                for k in keys:
                    per[k[2]][0] += R[a][k]["ops"]
                    per[k[2]][1] += main_rows[k]["ops"]
                p, ci, adj = ratio_ci(per, random.Random(f"20261022:{a}:{fam}:{bits}"))
                verdict = "fewer ops than main" if adj[1] < 1 else "more ops than main" if adj[0] > 1 else "not resolved"
                cell["arms"][a] = {"over_main": p, "ci95": ci, "ci_adjusted": adj, "verdict": verdict,
                                   "over_rho": sum(R[a][k]["ops"] for k in keys) / sum(main_rows[k]["rho_ops"] for k in keys)}
            best = min([("main", 1.0)] + [(a, e["over_main"]) for a, e in cell["arms"].items() if a != "cov"], key=lambda t: t[1])
            cell["best_table_arm"] = best[0]
            out["cells"][f"{fam}:{bits}"] = cell
    (HERE / "results.json").write_text(json.dumps(out, indent=1) + "\n")
    L = ["| family | bits | main r | main/rho | r16/main | r32/main | r64/main | cov/main | best table |", "|---|---|---|---|---|---|---|---|---|"]
    fmt = lambda e: "–" if e is None else f"{e['over_main']:.3f} [{e['ci_adjusted'][0]:.3f}, {e['ci_adjusted'][1]:.3f}]" + (" ✓" if e["verdict"].startswith("fewer") else " ✗" if e["verdict"].startswith("more") else "")
    for key, c in out["cells"].items():
        fam, bits = key.split(":")
        L.append(f"| {fam} | {bits} | {'/'.join(map(str, c['main_table_r']))} | {c['main_over_rho']:.3f} | "
                 + " | ".join(fmt(c["arms"].get(a)) for a in ("r16", "r32", "r64", "cov")) + f" | {c['best_table_arm']} |")
    (HERE / "results.md").write_text("Ratios of curve_solve group operations to main on the same targets; "
                                     f"intervals are {100 * (1 - ALPHA):.3f}% (Bonferroni over {K}); "
                                     "✓ fewer ops than main, ✗ more, unmarked not resolved.\n\n" + "\n".join(L) + "\n")
    print((HERE / "results.md").read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
