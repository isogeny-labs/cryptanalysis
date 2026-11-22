#!/usr/bin/env python3
"""L2 graph: per base CNF, geometric-mean conflict ratio B/A over its 3 shuffles,
against the A/A ratio A(k)/A(0); l = 4 UNSAT and SAT, plain and dual."""
import json, math, collections
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
rows = [json.loads(l) for l in open("rows.jsonl")]
by = collections.defaultdict(dict)
for r in rows: by[(r["file"], r["k"])][r["arm"]] = r
files = sorted(set(f for f, _ in by))
def gm(xs): return math.exp(sum(math.log(x) for x in xs) / len(xs))
fig, ax = plt.subplots(figsize=(10, 4.6))
x = 0; ticks = []
for f in files:
    if not f.startswith("l4"): continue
    rho = [by[(f, k)]["B"]["conflicts"] / by[(f, k)]["A"]["conflicts"] for k in range(3)]
    aa = [by[(f, k)]["A"]["conflicts"] / by[(f, 0)]["A"]["conflicts"] for k in (1, 2)]
    dec = by[(f, 0)]["A"]["decomposable"]
    c = "#2ca02c" if dec else ("#1f77b4" if "_plain_" in f else "#d62728")
    ax.scatter([x] * 3, rho, color=c, s=14, alpha=0.5)
    ax.scatter([x], [gm(rho)], color=c, s=60, marker="D")
    ax.scatter([x + 0.25] * 2, aa, color="grey", s=14, marker="x")
    ticks.append((x, f.replace(".cnf", "").replace("l4_", ""))); x += 1
ax.axhline(1, color="k", lw=0.8); ax.axhline(1 / 1.3, color="k", lw=0.8, ls="--")
ax.text(x - 0.5, 1 / 1.3, "success threshold 1/1.3", va="bottom", ha="right", fontsize=7)
ax.set_yscale("log"); ax.set_xticks([t[0] for t in ticks]); ax.set_xticklabels([t[1] for t in ticks], rotation=60, fontsize=7)
ax.set_ylabel("conflicts ratio (log)")
ax.set_title("L2, l = 4: SBVA→CaDiCaL / CaDiCaL per shuffle (dots), per file (diamond); grey × = A/A")
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([], [], color=c, marker="D", ls="", label=lab) for c, lab in
                   (("#1f77b4", "UNSAT plain"), ("#d62728", "UNSAT dual"), ("#2ca02c", "SAT (planted)"))] +
          [Line2D([], [], color="grey", marker="x", ls="", label="A/A: A(k)/A(0)")], fontsize=7, loc="lower left")
fig.tight_layout(); fig.savefig("l2_ratios.svg"); fig.savefig("l2_ratios.png", dpi=60)
