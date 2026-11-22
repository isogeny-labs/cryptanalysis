#!/usr/bin/env python3
"""L2c graph: per base CNF (l = 4, decomposable targets, fresh curve), conflict
ratio C/A per shuffle (dots) and per file (diamond), with A/A crosses."""
import json, math, collections
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
by = collections.defaultdict(dict)
for r in map(json.loads, open("rows.jsonl")): by[(r["file"], r["k"])][r["arm"]] = r
files = sorted(f for f in set(f for f, _ in by) if f.startswith("l4"))
gm = lambda xs: math.exp(sum(map(math.log, xs)) / len(xs))
fig, ax = plt.subplots(figsize=(11, 4.6))
for x, f in enumerate(files):
    rho = [by[(f, k)]["C"]["conflicts"] / by[(f, k)]["A"]["conflicts"] for k in range(3)]
    aa = [by[(f, k)]["A"]["conflicts"] / by[(f, 0)]["A"]["conflicts"] for k in (1, 2)]
    c = "#1f77b4" if "_plain_" in f else "#d62728"
    ax.scatter([x] * 3, rho, color=c, s=12, alpha=0.5); ax.scatter([x], [gm(rho)], color=c, s=55, marker="D")
    ax.scatter([x + 0.3] * 2, aa, color="grey", s=12, marker="x")
ax.axhline(1, color="k", lw=0.8); ax.axhline(1 / 1.3, color="k", lw=0.8, ls="--")
ax.set_yscale("log"); ax.set_xticks(range(len(files)))
ax.set_xticklabels([f.replace(".cnf", "").replace("l4_", "") for f in files], rotation=70, fontsize=6)
ax.set_ylabel("conflicts ratio (log)")
ax.set_title("L2c (confirmatory, fresh curve), l = 4 decomposable targets: RREF-augmented / base CNF; GM 0.631 [0.494, 0.809]")
ax.legend(handles=[Line2D([], [], color="#1f77b4", marker="D", ls="", label="plain"),
                   Line2D([], [], color="#d62728", marker="D", ls="", label="dual"),
                   Line2D([], [], color="grey", marker="x", ls="", label="A/A: A(k)/A(0)")], fontsize=7, loc="lower left")
fig.tight_layout(); fig.savefig("l2c_ratios.svg"); fig.savefig("l2c_ratios.png", dpi=60)
