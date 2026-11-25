#!/usr/bin/env python3
"""Confirmatory analysis frozen with PROTOCOL.md. Reads rows_main.jsonl.gz and
rows_c12.jsonl.gz, checks the invariants and writes results.json / results.md.
Exits non-zero, writing nothing, if any invariant fails."""
from __future__ import annotations

import gzip
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIMARY = (28, 30, 32, 34)
B = 10000
A_PRIMARY = 0.05 / 2      # two families
A_CELL = 0.05 / 16        # 2 families x 8 sizes, descriptive


def table_r(n: int, m: int, c: int) -> int:
    sqrt_nm = math.isqrt(n // m) + 1
    lg = n.bit_length()
    rr = 8
    while rr * 2 <= sqrt_nm // (c * lg) and rr * 2 <= 32:
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


def q(sorted_vals, a):
    return sorted_vals[min(len(sorted_vals) - 1, max(0, int(a * len(sorted_vals))))]


def main() -> int:
    M, P = load("main"), load("c12")
    fail = []
    if set(M) != set(P):
        fail.append("grids differ")
    for k, x in M.items():
        y = P.get(k)
        if y is None:
            continue
        if (x["p"], x["a"], x["b"], x["k"]) != (y["p"], y["a"], y["b"], y["k"]):
            fail.append(f"different curve/target at {k}")
            break
    if not all(x["correct"] for x in M.values()) or not all(x["correct"] for x in P.values()):
        fail.append("wrong answers")
    if not all(x.get("rho_correct") for x in M.values()):
        fail.append("rho reference wrong or missing")
    same, differ = 0, 0
    for k, x in M.items():
        m = 4 if k[0] == "j1728" else 6
        if table_r(x["r"], m, 48) == table_r(x["r"], m, 12):
            same += 1
            differ += P[k]["ops"] != x["ops"]
    if differ:
        fail.append(f"identity control: {differ} of {same} rows differ where both rules pick the same table")
    if fail:
        print("INVARIANT FAILURE:\n  " + "\n  ".join(fail))
        return 1

    per = defaultdict(lambda: defaultdict(lambda: [0, 0]))   # (fam, bits) -> curve -> [c12, main]
    for k, x in M.items():
        c = per[(k[0], k[1])][k[2]]
        c[0] += P[k]["ops"]
        c[1] += x["ops"]
    out = {"identity_control": {"rows_with_equal_table": same, "differing": differ}, "primary": {}, "cells": {}}
    rng = random.Random("20261023:confirm")
    for fam in ("j1728", "j0"):
        cells = {b: list(per[(fam, b)].values()) for b in sorted({k[1] for k in M})}
        ratio = lambda v, idx: sum(v[i][0] for i in idx) / sum(v[i][1] for i in idx)
        boots = {b: [] for b in cells}
        for _ in range(B):
            for b, v in cells.items():
                boots[b].append(ratio(v, [rng.randrange(len(v)) for _ in v]))
        point = {b: ratio(v, range(len(v))) for b, v in cells.items()}
        gm = lambda vals: math.exp(sum(math.log(x) for x in vals) / len(vals))
        gm_boot = sorted(gm([boots[b][i] for b in PRIMARY]) for i in range(B))
        gm_point = gm([point[b] for b in PRIMARY])
        ci = (q(gm_boot, A_PRIMARY / 2), q(gm_boot, 1 - A_PRIMARY / 2))
        out["primary"][fam] = {"geomean_28_34": gm_point, "ci": ci, "level": 1 - A_PRIMARY,
                               "verdict": "confirmed: fewer ops than main" if ci[1] < 1 else "not confirmed"}
        for b, v in cells.items():
            s = sorted(boots[b])
            keys = [k for k in M if k[0] == fam and k[1] == b]
            m = 4 if fam == "j1728" else 6
            out["cells"][f"{fam}:{b}"] = {
                "c12_over_main": point[b], "ci_cell": (q(s, A_CELL / 2), q(s, 1 - A_CELL / 2)), "curves": len(v),
                "tables_main": sorted({table_r(M[k]["r"], m, 48) for k in keys}),
                "tables_c12": sorted({table_r(M[k]["r"], m, 12) for k in keys}),
                "main_over_rho": sum(M[k]["ops"] for k in keys) / sum(M[k]["rho_ops"] for k in keys),
                "c12_over_rho": sum(P[k]["ops"] for k in keys) / sum(M[k]["rho_ops"] for k in keys)}
    (HERE / "results.json").write_text(json.dumps(out, indent=1) + "\n")
    L = ["## Primary (geometric mean of the 28, 30, 32, 34-bit cell ratios, c = 12 over main)", "",
         "| family | ratio | 97.5% interval | verdict |", "|---|---|---|---|"]
    for fam, e in out["primary"].items():
        L.append(f"| {fam} | {e['geomean_28_34']:.4f} | [{e['ci'][0]:.4f}, {e['ci'][1]:.4f}] | {e['verdict']} |")
    L += ["", "## Cells (descriptive; 99.69% intervals, Bonferroni over 16)", "",
          "| family | bits | tables main → c12 | c12/main | interval | main/rho | c12/rho |", "|---|---|---|---|---|---|---|"]
    for key, c in out["cells"].items():
        fam, b = key.split(":")
        L.append(f"| {fam} | {b} | {'/'.join(map(str, c['tables_main']))} → {'/'.join(map(str, c['tables_c12']))} | {c['c12_over_main']:.3f} | "
                 f"[{c['ci_cell'][0]:.3f}, {c['ci_cell'][1]:.3f}] | {c['main_over_rho']:.3f} | {c['c12_over_rho']:.3f} |")
    L += ["", f"Identity control: {same} rows where both rules pick the same table, {differ} differing."]
    (HERE / "results.md").write_text("\n".join(L) + "\n")
    print((HERE / "results.md").read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
