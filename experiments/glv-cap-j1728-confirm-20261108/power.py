#!/usr/bin/env python3
"""Power calculation frozen with PROTOCOL.md (normal approximation; no data involved)."""
import math
from statistics import NormalDist
Z = NormalDist().inv_cdf
V = 0.53                      # per-target variance of log(arm/ref): 0.48-0.54 in #1340's j=1728 cells, 0.51-0.56 in #1339's
for n in (1600, 2400, 3000, 3600):
    se = math.sqrt(V / (4 * n))      # pooled over 4 sizes, equal weight, one target per curve
    hw = Z(0.9875) * se
    row = [f"n={n:5d}/cell  SE={se:.4f}  97.5% half-width={100*hw:.2f}%"]
    for ratio in (0.968, 0.975, 0.98, 0.985, 0.99, 1.0):
        row.append(f"P({ratio})={1 - NormalDist(math.log(ratio), se).cdf(-hw):.2f}" if False else
                   f"P({ratio})={NormalDist(math.log(ratio), se).cdf(-hw):.2f}")
    print("  ".join(row))
n = 3000
se1 = math.sqrt(V / n)
print(f"per size (n={n}): SE={se1:.4f}; Bonferroni 98.75% half-width={100 * Z(0.99375) * se1:.2f}%")
print(f"S2 j=0, n=800/cell: SE={math.sqrt(V/3200):.4f}; 97.5% half-width={100*Z(0.9875)*math.sqrt(V/3200):.2f}%")
