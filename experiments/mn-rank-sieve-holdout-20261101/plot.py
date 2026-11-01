#!/usr/bin/env python3
"""Render figure.svg/png and report.pdf from result.json (+ run.py's scratch arrays)."""
import json, textwrap
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
r = json.load(open("result.json"))
sc = np.load("/tmp/_mn_scatter.npy")
fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
ax[0].hexbin(sc[0], sc[1], gridsize=60, bins="log", cmap="Greys", rasterized=True)
ax[0].set(xlabel="screen MN score (primes 5-397)", ylabel="held-out MN score (primes 401-1193)",
          title=f"Screen vs held-out, corr = {r['corr_screen_holdout']:.1e}")
labs = [f"prune {p['keep_fraction']}" for p in r["pruning"]] + ["early abort"]
ys = [p["yield_per_compute_vs_screen"] for p in r["pruning"]] + [r["early_abort"]["recall_vs_screen"] / 0.01]
yh = [p["holdout_top0.1pct_enrichment"] for p in r["pruning"]] + [r["early_abort"]["holdout_top0.1pct_enrichment"]]
x = np.arange(len(labs)); w = 0.38
ax[1].bar(x - w/2, ys, w, label="enrichment on the screen score (circular)", color="#bbbbbb")
ax[1].bar(x + w/2, yh, w, label="enrichment on held-out primes", color="#d55e00")
ax[1].axhline(1, color="k", lw=.8, ls="--"); ax[1].set_yscale("log")
ax[1].set_xticks(x, labs); ax[1].set_ylabel("top-curve yield per unit compute (x)")
ax[1].set_title("The speed-ups enrich only the score they filter on"); ax[1].legend(fontsize=8)
pc = r["positive_control_holdout_mean_t_le_1e6"]
names = ["test family\n(t^3+5)", "positive control\n(rank>=1, point (0,t))", "test family top-100\nby screen"]
m = [pc["test"]["mean"], pc["posctl_r1"]["mean"], r["holdout_top_by_screen"]["mean"]]
e = [2*pc["test"]["se"], 2*pc["posctl_r1"]["se"], 2*r["holdout_top_by_screen"]["se"]]
ax[2].bar(range(3), m, yerr=e, color=["#999999", "#0072b2", "#d55e00"], capsize=4)
ax[2].set_xticks(range(3), names, fontsize=8); ax[2].set_ylabel("mean held-out MN score (±2 SE)")
ax[2].set_title("Instrument sees rank; top screen curves do not")
fig.tight_layout(); fig.savefig("figure.svg"); fig.savefig("figure.png", dpi=80)
from PIL import Image; Image.open("figure.png").convert("RGB").quantize(64).save("figure.png", optimize=True)
matplotlib.rcParams["savefig.dpi"] = 60; matplotlib.rcParams["pdf.fonttype"] = 42; matplotlib.rcParams["font.family"] = "DejaVu Sans"; matplotlib.rcParams["pdf.compression"] = 9
with PdfPages("report.pdf") as pdf:
    pf = plt.figure(figsize=(14, 4.2)); pf.figimage(plt.imread("figure.png"), resize=True); pdf.savefig(pf)
    tf = plt.figure(figsize=(8.5, 11)); tf.text(0.06, 0.97, open("RESULT.md").read(), va="top",
        fontsize=6.0, wrap=True); pdf.savefig(tf)
print("ok")
