"""Plot the PS-5 operation counts and replay coverage.  Rendering only: every
number is read from raw/ (the emitter's and the parity runner's JSON).

    python3 plot_ps5.py        -> figures/ps5_ops_and_coverage.svg
"""
import glob
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")


def load_jsonl(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("{"):
                rows.append(json.loads(line))
    return rows


emit = {}
for p in glob.glob(os.path.join(RAW, "emit", "emit_l*.json")):
    d = json.load(open(p))
    emit[d["l"]] = d
parity = {}
for p in glob.glob(os.path.join(RAW, "parity_l*.jsonl")):
    if p.endswith("_model.jsonl"):
        continue
    rows = load_jsonl(p)
    if rows:
        parity[rows[-1]["l"]] = rows[-1]

ls = sorted(emit)
tasks = 8
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)

# Panel a: gates per pair-slot (program gates / tasks), by kind.
kinds = [("xand", "xor-and (1 lop3, 2 two-input ops)", "#1f77b4"), ("xor", "xor", "#ff7f0e"),
         ("and", "and", "#2ca02c"), ("or", "or", "#9467bd"), ("not", "not", "#8c564b")]
bottom = [0.0] * len(ls)
for key, label, color in kinds:
    vals = [emit[l][key] / tasks for l in ls]
    ax[0].bar([str(l) for l in ls], vals, bottom=bottom, label=label, color=color, width=0.62)
    bottom = [b + v for b, v in zip(bottom, vals)]
for i, l in enumerate(ls):
    ax[0].text(i, bottom[i] + 250, f"{bottom[i]:,.1f}", ha="center", fontsize=9)
ax[0].set_xlabel("rung l (n = 3l)")
ax[0].set_ylabel("lop3 issues per lane (= program gates / 8 tasks)")
ax[0].set_title("a. Counted gates per lane slot, PS-3 program (fused)")
ax[0].legend(fontsize=8, frameon=False, loc="upper left")
ax[0].set_ylim(0, max(bottom) * 1.18)

# Panel b: pairs replayed through the emulation, 80 targets per rung.
pl = sorted(parity)
pairs = [parity[l]["pairs_replayed"] for l in pl]
ax[1].bar([str(l) for l in pl], pairs, color="#2e7d32", width=0.62)
ax[1].set_yscale("log")
for i, l in enumerate(pl):
    r = parity[l]
    ax[1].text(i, pairs[i] * 1.25,
               f"{r['hit_lanes_confirmed']} hit lanes\n{r['mismatches']} mismatches",
               ha="center", fontsize=8)
ax[1].set_ylim(min(pairs) / 3, max(pairs) * 12)
ax[1].set_xlabel("rung l")
ax[1].set_ylabel("pairs replayed (80 targets per rung)")
ax[1].set_title("b. PS-0 corpus replayed through the CPU emulation")

fig.suptitle("PS-5: CPU emulation of the GPU kernel (no device was used; nothing here is a GPU measurement)",
             fontsize=10)
os.makedirs(os.path.join(HERE, "figures"), exist_ok=True)
out = os.path.join(HERE, "figures", "ps5_ops_and_coverage.svg")
fig.savefig(out)
print("wrote", out)
