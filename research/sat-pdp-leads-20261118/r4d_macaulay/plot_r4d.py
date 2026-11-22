#!/usr/bin/env python3
"""Round-4 D graph: certified linear relations L vs L_max by bidegree, real vs controls."""
import json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
rows = [json.loads(l) for l in open("rows.jsonl")] + [json.loads(l) for l in open("amendment_planted_n17_22.jsonl")]
bds = [(1, 1), (1, 2), (2, 1), (2, 2)]
fig, axs = plt.subplots(1, 2, figsize=(10, 3.8), sharey=False)
for ax, (n, l) in zip(axs, [(13, 4), (17, 5)]):
    for kind, c, mk in (("real", "#d62728", "o"), ("null", "grey", "x"), ("planted", "#2ca02c", "s")):
        xs, ys = [], []
        for i, bd in enumerate(bds):
            for r in rows:
                if r["kind"] == kind and r["n"] == n and (r["A"], r["B"]) == bd:
                    xs.append(i + {"real": -0.15, "null": 0, "planted": 0.15}[kind]); ys.append(r["L"])
        ax.scatter(xs, ys, color=c, marker=mk, label=kind + (" (positive control)" if kind == "planted" else ""))
    lm = sorted({r["L_max"] for r in rows if r["kind"] == "real" and r["n"] == n})
    ax.axhspan(min(lm), max(lm), color="#d62728", alpha=0.12, label=f"real L_max {min(lm)}-{max(lm)}")
    ax.set_xticks(range(4)); ax.set_xticklabels([str(b) for b in bds]); ax.set_xlabel("bidegree (t, q)")
    ax.set_title(f"n = {n}, l = {l}"); ax.set_ylabel("certified linear relations L")
axs[0].legend(fontsize=7, loc="upper left")
fig.suptitle("Round-4 D: Macaulay matrices certify L = 1 on the real leaf system (null: 0); solved control reaches L_max", fontsize=9)
fig.tight_layout(); fig.savefig("r4d_L.svg"); fig.savefig("r4d_L.png", dpi=70)
