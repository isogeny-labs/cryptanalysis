"""Render the ic-parallel report: strong scaling and before/after cell wall.

usage: report.py DATA_DIR OUT_DIR   (DATA_DIR holds scaling/ and before_after/)
"""
import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

data, out = sys.argv[1], sys.argv[2]
summ = json.load(open(f"{data}/scaling/scaling_summary.json"))
ba = json.load(open(f"{data}/before_after/before_after.json"))

f1, ax = plt.subplots(figsize=(6.4, 4.2))
for cfg in dict.fromkeys(s["config"] for s in summ):
    rows = [s for s in summ if s["config"] == cfg]
    t = [r["threads"] for r in rows]
    y = [r["collector_speedup"] for r in rows]
    lo = [r["collector_speedup"] - r["ci95"][0] for r in rows]
    hi = [r["ci95"][1] - r["collector_speedup"] for r in rows]
    ax.errorbar(t, y, yerr=[lo, hi], marker="o", capsize=3, label=cfg)
ax.plot([1, 4], [1, 4], ls="--", c="grey", lw=0.8, label="linear")
ax.set_xlabel("--threads"); ax.set_ylabel("relation-phase speedup vs --threads 1")
ax.set_xticks([1, 2, 3, 4]); ax.legend(fontsize=7); ax.grid(alpha=0.3)
ax.set_title("ic bench --threads: counts identical in every run", fontsize=9)
f1.tight_layout(); f1.savefig(f"{out}/scaling.svg")

f2, ax = plt.subplots(figsize=(6.4, 4.2))
cells = [r["cell"] for r in ba]
x = range(len(cells))
ax.bar([i - 0.2 for i in x], [r["previous_wall_s"] for r in ba], 0.4, label="previous binary (6b64ee6)")
ax.bar([i + 0.2 for i in x], [r["this_wall_s"] for r in ba], 0.4, label="this branch")
ax.set_yscale("log"); ax.set_xticks(list(x)); ax.set_xticklabels(cells)
ax.set_ylabel("whole ic bench process, seconds (log)")
for i, r in enumerate(ba):
    ax.text(i, max(r["previous_wall_s"], r["this_wall_s"]) * 1.3, f'{r["speedup"]}x', ha="center", fontsize=8)
ax.set_title("Phase-3 registry cells, --threads 1, same counts", fontsize=9)
ax.legend(fontsize=7); f2.tight_layout(); f2.savefig(f"{out}/before_after.svg")

with PdfPages(f"{out}/report.pdf") as pdf:
    ft = plt.figure(figsize=(8.27, 11.69)); ft.text(0.07, 0.95, "ic: parallel relation phase and O(q^1/4) instance search", fontsize=13, va="top")
    lines = ["Host: 4-vCPU cloud VM (exploratory tier, not isolated).", "",
             "Before/after (registry phase-3 cells, 8 repeats, 16 rho runs):"]
    lines += [f'  {r["cell"]:11s} {r["previous_wall_s"]:8.2f} s -> {r["this_wall_s"]:6.2f} s  ({r["speedup"]}x)  same counts: {r["same_counts"]}' for r in ba]
    lines += ["", "Relation phase, --threads N vs 1 (geometric mean of 5 interleaved pairs, 95% bootstrap CI):"]
    lines += [f'  {s["config"]:22s} t={s["threads"]}  {s["collector_speedup"]:.2f}x [{s["ci95"][0]:.2f}, {s["ci95"][1]:.2f}]  counts identical: {s["counts_identical_to_t1"]}' for s in summ if s["threads"] > 1]
    lines += ["  (koblitz43 / mitm2 measured at 94fa0d6, whose in-loop gate sent cheap oracles to the slower",
              "   split loop; 77e4f1d decides before the run and runs the --threads 1 loop for them.)"]
    lines += ["", "S is unchanged by construction: every integer counter, row and recovered", "logarithm equals --threads 1 (and the previous binary). Counters priced in", "measured nanoseconds (descent-algebraic) read high under contention."]
    ft.text(0.07, 0.90, "\n".join(lines), fontsize=8, family="monospace", va="top"); pdf.savefig(ft)
    pdf.savefig(f1); pdf.savefig(f2)
print("wrote", out)
