#!/usr/bin/env python3
"""POST-HOC (not part of the frozen analysis): price main's table rule with other
constants c (r doubles while 2r <= sqrt(n/m) / (c * log2 n), cap `cap`) on this
round's rows. Each target's cost at table size r is read from the arm that ran
that size (main where main's own rule picks r). Output: rule_search.json."""
import gzip, json, math, sys
from collections import defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent

def rule(n, m, c, cap):
    s = math.isqrt(n // m) + 1; lg = n.bit_length(); rr = 8
    while rr * 2 <= s // (c * lg) and rr * 2 <= cap: rr *= 2
    return rr

rows = {}
for arm in ("main", "r16", "r32", "r64"):
    for l in gzip.open(HERE / f"rows_{arm}.jsonl.gz", "rt"):
        x = json.loads(l); rows.setdefault((x["family"], x["bits"], x["curve"], x["target"]), {})[arm] = x
out = {}
for cap in (32, 64):
    for c in (8, 12, 16, 20, 24, 32, 48):
        cells = defaultdict(lambda: [0, 0]); missing = 0; picks = defaultdict(lambda: defaultdict(int))
        for k, a in rows.items():
            m = 4 if k[0] == "j1728" else 6; n = a["main"]["r"]
            auto, want = rule(n, m, 48, 32), rule(n, m, c, cap)
            src = "main" if want == auto else {16: "r16", 32: "r32", 64: "r64"}.get(want)
            if src is None: missing += 1; continue
            cells[(k[0], k[1])][0] += a[src]["ops"]; cells[(k[0], k[1])][1] += a["main"]["ops"]
            picks[(k[0], k[1])][want] += 1
        ratios = {f"{f}:{b}": v[0] / v[1] for (f, b), v in sorted(cells.items())}
        gm = math.exp(sum(math.log(v) for v in ratios.values()) / len(ratios))
        out[f"c={c},cap={cap}"] = {"geomean_over_main": gm, "unavailable_rows": missing, "cells": ratios,
                                   "picks": {f"{f}:{b}": dict(p) for (f, b), p in sorted(picks.items())}}
        print(f"c={c:2d} cap={cap}: geomean {gm:.4f}  missing {missing}  " + " ".join(f"{k.split(':')[0][:2]}{k.split(':')[1]}={v:.3f}" for k, v in ratios.items()))
(HERE / "rule_search.json").write_text(json.dumps(out, indent=1) + "\n")
