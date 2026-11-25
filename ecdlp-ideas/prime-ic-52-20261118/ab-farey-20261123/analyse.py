#!/usr/bin/env python3
"""
analyse.py — reduction of raw/cells.json for the report.

(1) exact-identity checks (tuples = C(N+m-1,m), sum r = tuples, r(O) = N/2 at m=2)
(2) shape comparison at equal |F|, with binomial standard errors on the only
    quantity that is not fixed by the counting identity: the fraction of
    targets with a relation
(3) H6: the sign-redundant pair list inflates ordered hit counts by exactly 2^m
"""
import json
import math
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "raw")
cells = json.load(open(os.path.join(RAW, "cells.json")))
SHAPES = {0: "interval", 1: "farey", 2: "random"}


def choose(k, m):
    return math.comb(k + m - 1, m)


print("== (1) exact identities ==")
bad = 0
for c in cells:
    N, m, n = c["N"], c["m"], c["n"]
    ok_t = c["tuples"] == choose(N, m)
    ok_s = c["sum_r"] == c["tuples"]
    ok_O = (c["r_at_O"] == N // 2) if m == 2 else True
    ok = ok_t and ok_s and ok_O
    bad += 0 if ok else 1
    print(f"p={c['p']} N={N} m={m} {SHAPES[c['shape']]:>8}  "
          f"tuples {c['tuples']} == C(N+m-1,m) {choose(N, m)}: {ok_t} | "
          f"sum_r: {ok_s} | r(O)={c['r_at_O']}"
          + (f" == N/2={N//2}: {ok_O}" if m == 2 else ""))
print("all exact identities hold:", bad == 0)

print("\n== (2) shape comparison at equal |F| ==")
groups = defaultdict(dict)
for c in cells:
    groups[(c["p"], c["m"], c["N"])][SHAPES[c["shape"]]] = c
for key in sorted(groups):
    p, m, N = key
    gz = groups[key]
    n = next(iter(gz.values()))["n"]
    row = []
    for s in ("interval", "farey", "random"):
        c = gz[s]
        f = c["nz_exclO"] / (n - 1)
        sd = math.sqrt(f * (1 - f) / (n - 1))
        row.append((s, f, sd, c["max_r_exclO"], c["sum_r2_exclO"] / (n - 1)))
    print(f"\n p={p} m={m} N={N}  (group order {n:,}, targets {n-1:,})")
    for s, f, sd, mx, m2 in row:
        print(f"   {s:>8}: P(r>=1)={f:.5f} +-{sd:.5f}  max={mx}  E[r^2]={m2:.4f}")
    fi, ff, fr = row[0][1], row[1][1], row[2][1]
    sd = row[0][2]
    print(f"   farey - interval = {ff-fi:+.5f}  ({(ff-fi)/sd:+.1f} sd)")
    print(f"   random - farey   = {fr-ff:+.5f}  ({(fr-ff)/sd:+.1f} sd)")

print("\n== (3) H6: sign-redundant pair list inflates hits by 2^m ==")
# purely combinatorial: base elements duplicated, ordered tuples, fixed targets
import random
rng = random.Random(11)
n = 1009
base = rng.sample(range(n), 40)
T = set(rng.sample(range(n), 200))
for m in (2, 3):
    hits_dedup = sum(1 for tup in __import__("itertools").product(base, repeat=m)
                     if sum(tup) % n in T)
    base2 = base + base
    hits_dup = sum(1 for tup in __import__("itertools").product(base2, repeat=m)
                   if sum(tup) % n in T)
    print(f"  m={m}: hits(deduped)={hits_dedup} hits(2x list)={hits_dup} "
          f"ratio={hits_dup/hits_dedup if hits_dedup else float('nan'):.4f} "
          f"(2^m = {2**m})  distinct relations unchanged: "
          f"{sorted(set(tuple(sorted(t)) for t in __import__('itertools').product(base2, repeat=m) if sum(t) % n in T)) == sorted(set(tuple(sorted(t)) for t in __import__('itertools').product(base, repeat=m) if sum(t) % n in T))}")
