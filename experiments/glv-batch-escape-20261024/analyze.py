#!/usr/bin/env python3
"""Paired analysis of PROTOCOL.md: python3 analyze.py rows_main.jsonl rows_batch.jsonl results.json"""
from __future__ import annotations

import collections
import json
import sys

import numpy as np

PRICES = (1.0, 2.5, 5.0)  # d: cost, in field multiplications, of one division step of an inversion
SQR = 0.8                 # a squaring costs 0.8 multiplications
PHASES = ("setup", "batch", "post", "escape", "restart")
BOOT = 10000
ALPHA = 0.05
M_INTERVALS = 12 * 3      # Bonferroni: 12 cells x 3 prices


def load(path):
    rows = {}
    for line in open(path):
        r = json.loads(line)
        rows[(r["family"], r["bits"], r["curve"], r["target"])] = r
    return rows


def cost(r, d):
    return sum(r[f"{p}_mul"] + SQR * r[f"{p}_sqr"] + d * r[f"{p}_euclid"] for p in PHASES)


def metric(r, name):
    if name.startswith("cost"):
        return cost(r, float(name[4:]))
    if name == "inv":
        return sum(r[f"{p}_inv"] for p in PHASES)
    if name == "mul":
        return sum(r[f"{p}_mul"] + r[f"{p}_sqr"] for p in PHASES)
    return r[name]


def ratio_ci(by_curve, name, rng, level):
    """ratio of sums (candidate / main) and a percentile bootstrap interval over curves."""
    curves = list(by_curve)
    num = np.array([sum(metric(b, name) for a, b in by_curve[c]) for c in curves], dtype=float)
    den = np.array([sum(metric(a, name) for a, b in by_curve[c]) for c in curves], dtype=float)
    est = num.sum() / den.sum()
    idx = rng.integers(0, len(curves), size=(BOOT, len(curves)))
    reps = num[idx].sum(axis=1) / den[idx].sum(axis=1)
    lo, hi = np.quantile(reps, [level / 2, 1 - level / 2])
    return float(est), float(lo), float(hi)


def main():
    main_rows, cand_rows, out = load(sys.argv[1]), load(sys.argv[2]), sys.argv[3]
    assert main_rows.keys() == cand_rows.keys(), "arms differ in curves/targets"
    cells = collections.defaultdict(lambda: collections.defaultdict(list))
    for key, a in main_rows.items():
        assert (a["p"], a["a"], a["b"], a["k"]) == tuple(cand_rows[key][x] for x in ("p", "a", "b", "k"))
        cells[(key[0], key[1])][key[2]].append((a, cand_rows[key]))
    level = ALPHA / M_INTERVALS
    rng = np.random.default_rng(20261025)
    res = {"level": level, "intervals": M_INTERVALS, "correct_main": all(r["correct"] for r in main_rows.values()),
           "correct_candidate": all(r["correct"] for r in cand_rows.values()), "n_solves": len(main_rows), "cells": {}}
    for cell, by_curve in sorted(cells.items()):
        c = {"curves": len(by_curve), "solves": sum(len(v) for v in by_curve.values())}
        for name in ("cost1.0", "cost2.5", "cost5.0", "ops", "inv", "mul"):
            e, lo, hi = ratio_ci(by_curve, name, rng, level)
            c[name] = {"ratio": e, "lo": lo, "hi": hi}
        allp = [(a, b) for v in by_curve.values() for a, b in v]
        c["escapes_main"] = sum(a["esc2"] + a["esc4"] for a, b in allp)
        c["escapes_candidate"] = sum(b["esc2"] + b["esc4"] for a, b in allp)
        c["steps_main"] = sum(a["batch_walks"] for a, b in allp)
        c["win"] = all(c[f"cost{d}"]["hi"] < 1 for d in ("1.0", "2.5", "5.0"))
        c["regress"] = any(c[f"cost{d}"]["lo"] > 1 for d in ("1.0", "2.5", "5.0"))
        res["cells"][f"{cell[0]}:{cell[1]}"] = c
    res["wins"] = sum(c["win"] for c in res["cells"].values())
    res["regressions"] = sum(c["regress"] for c in res["cells"].values())
    json.dump(res, open(out, "w"), indent=1)
    print(f"correct main={res['correct_main']} candidate={res['correct_candidate']} solves={res['n_solves']}")
    for k, c in res["cells"].items():
        print(k, " ".join(f"{n} {c[n]['ratio']:.5f} [{c[n]['lo']:.5f},{c[n]['hi']:.5f}]"
                          for n in ("cost1.0", "cost2.5", "cost5.0", "ops")), "WIN" if c["win"] else "", "REGRESS" if c["regress"] else "")
    print("wins", res["wins"], "regressions", res["regressions"])


if __name__ == "__main__":
    main()
