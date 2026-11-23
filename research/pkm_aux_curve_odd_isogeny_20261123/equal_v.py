#!/usr/bin/env python3
"""Branch A: odd-degree vs degree-2 isogeny towers at equal |V|.

Reads pilot rows (isogeny kind, control tower, random targets only: a
refutation's work is fixed by the system's shape, planted rows stop early).
Reference: degree-2 isogeny rows. For each lead row at log2|V| = L, the
reference's log(cost) is interpolated linearly in L between the two nearest
completed reference sizes (no extrapolation). Costs: wall ms and max_cols.
A timed-out row is not a measurement of its cost and is skipped (its size
is reported as the frontier).

Usage: equal_v.py REF.jsonl[,REF2...] LEAD.jsonl [LEAD2 ...]
"""
import collections
import json
import math
import sys


def load(paths):
    by = collections.defaultdict(list)
    frontier = {}
    for path in paths:
        for line in open(path):
            r = json.loads(line)
            if "summary" in r or r.get("kind") != "isogeny" or r.get("control") != "tower":
                continue
            degs = tuple(sorted(set(r.get("iso_degrees") or [2])))
            if r["target"] != "random":
                continue
            L = r.get("log2_V", r["t"])
            k = (r["m"], degs)
            if r["timed_out"]:
                frontier[k] = min(frontier.get(k, 1e9), L)
                continue
            by[(k, L)].append(r)
    pts = collections.defaultdict(dict)
    for (k, L), rs in by.items():
        pts[k][L] = (sum(r["ms"] for r in rs) / len(rs), max(r["max_cols"] for r in rs), len(rs))
    return pts, frontier


def interp(curve, L, idx):
    xs = sorted(curve)
    for lo, hi in zip(xs, xs[1:]):
        if lo <= L <= hi:
            ylo, yhi = math.log(max(curve[lo][idx], 1e-3)), math.log(max(curve[hi][idx], 1e-3))
            return math.exp(ylo + (yhi - ylo) * (L - lo) / (hi - lo))
    return None


def main():
    ref_pts, ref_front = load(sys.argv[1].split(","))
    lead_pts, lead_front = load(sys.argv[2:])
    print("| m | degrees | log2 V | lead ms | ref ms (interp) | ms ratio ref/lead | lead max_cols | ref max_cols (interp) | cols ratio |")
    print("|--:|:--|--:|--:|--:|--:|--:|--:|--:|")
    for (m, degs), curve in sorted(lead_pts.items()):
        if degs == (2,):
            continue
        ref = ref_pts.get((m, (2,)), {})
        for L in sorted(curve):
            ms, cols, n = curve[L]
            rms, rcols = interp(ref, L, 0), interp(ref, L, 1)
            f = lambda x: "-" if x is None else f"{x:,.0f}"
            g = lambda a, b: "-" if a is None else f"{a / max(b, 1e-3):.2f}"
            print(f"| {m} | {','.join(map(str, degs))} | {L:.2f} | {ms:,.1f} | {f(rms)} | {g(rms, ms)} | {cols:,} | {f(rcols)} | {g(rcols, cols)} |")
    print()
    print("Frontier (smallest log2|V| at which a random-target refutation timed out):")
    for k in sorted(set(ref_front) | set(lead_front)):
        print(f"  m={k[0]} degrees={','.join(map(str, k[1]))}: {ref_front.get(k, lead_front.get(k)):.2f}")


if __name__ == "__main__":
    main()
