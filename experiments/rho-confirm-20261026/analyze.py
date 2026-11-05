#!/usr/bin/env python3
"""Frozen analysis: analyze.py main_rows.jsonl[.gz] candidate_rows.jsonl[.gz] [--out DIR].

Per size: ratio of sums candidate / main over all targets; bootstrap over curves (curves
resampled with replacement, 10,000 resamples, numpy seed 20261026).  Pooled: geometric mean of the
per-size ratios; its interval is the 2.5% and 97.5% percentiles (one primary comparison).
Per-size intervals are Bonferroni-adjusted over the 6 sizes (0.4167% and 99.5833% percentiles)."""
import gzip, json, math, sys
from collections import defaultdict
from pathlib import Path
import numpy as np

def load(p):
    return [json.loads(l) for l in (gzip.open if p.endswith(".gz") else open)(p, "rt")]

args = [a for a in sys.argv[1:] if not a.startswith("--")]
out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else Path(".")
if "--out" in sys.argv: args.remove(str(out))
A, B = load(args[0]), load(args[1])
key = lambda r: (r["bits"], r["curve"], r["target"])
ma, mb = {key(r): r for r in A}, {key(r): r for r in B}
assert ma.keys() == mb.keys() and all(ma[k]["p"] == mb[k]["p"] and ma[k]["a"] == mb[k]["a"] for k in ma), "arms not paired"
ok = all(r["ok"] for r in A + B)
sizes = sorted({k[0] for k in ma})
rng = np.random.default_rng(20261026)
BOOT = 10000
cell, logs = {}, []
for b in sizes:
    cs = sorted({k[1] for k in ma if k[0] == b})
    num = np.array([sum(mb[k]["ops"] for k in ma if k[0] == b and k[1] == c) for c in cs], float)
    den = np.array([sum(ma[k]["ops"] for k in ma if k[0] == b and k[1] == c) for c in cs], float)
    idx = rng.integers(0, len(cs), size=(BOOT, len(cs)))
    bs = num[idx].sum(1) / den[idx].sum(1)
    S_main = float(np.mean([ma[k]["ops"] / math.sqrt(ma[k]["order"]) for k in ma if k[0] == b]))
    S_cand = float(np.mean([mb[k]["ops"] / math.sqrt(mb[k]["order"]) for k in ma if k[0] == b]))
    cell[b] = {"ratio": float(num.sum() / den.sum()), "lo": float(np.percentile(bs, 100 * 0.05 / 6 / 2)),
               "hi": float(np.percentile(bs, 100 * (1 - 0.05 / 6 / 2))), "S_main": S_main, "S_candidate": S_cand}
    logs.append(np.log(bs))
pb = np.exp(np.mean(logs, axis=0))
pooled = math.exp(np.mean([math.log(cell[b]["ratio"]) for b in sizes]))
res = {"pooled": pooled, "pooled_lo": float(np.percentile(pb, 2.5)), "pooled_hi": float(np.percentile(pb, 97.5)), "cells": cell,
       "all_correct": ok, "solves_per_arm": len(ma)}
res["confirmed"] = bool(ok and res["pooled_hi"] < 1 and all(cell[b]["lo"] <= 1 for b in sizes))
(out / "results.json").write_text(json.dumps(res, indent=1))
L = ["| size | main S | candidate S | ratio candidate / main | interval (Bonferroni over 6) |", "|---|---|---|---|---|"]
for b in sizes:
    c = cell[b]; L.append(f"| {b} bits | {c['S_main']:.3f} | {c['S_candidate']:.3f} | {c['ratio']:.4f} | [{c['lo']:.4f}, {c['hi']:.4f}] |")
L += ["", f"Pooled ratio {pooled:.4f}, 95% interval [{res['pooled_lo']:.4f}, {res['pooled_hi']:.4f}]; all logarithms correct: {ok}; confirmed: {res['confirmed']}"]
(out / "results.md").write_text("\n".join(L) + "\n"); print("\n".join(L))
