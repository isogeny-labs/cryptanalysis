"""Lay out the recorded values in data/measurements.json (plotting only)."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
M = json.loads((HERE / "data" / "measurements.json").read_text())
(HERE / "figures").mkdir(exist_ok=True)
fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(12.5, 3.9))

hist = {k: v for k, v in M["ir_per_op_history_seed2"].items() if k != "target"}
names = list(hist)
v = [hist[n] for n in names]
a1.bar([n.replace(" (", "\n(") for n in names], v, color=["#999999", "#555555", "#2f6db3"])
a1.axhline(M["ir_per_op_history_seed2"]["target"], color="#c0392b", lw=1, ls="--")
a1.text(2.45, 101.5, "target < 100", color="#c0392b", fontsize=7, ha="right")
for i, x in enumerate(v):
    a1.text(i, x + 2, f"{x:.1f}", ha="center", fontsize=8)
a1.set_ylim(0, 145)
a1.set_ylabel("Callgrind Ir per group operation", fontsize=8)
a1.set_title("Whole Z_p rho solve, seed 2 (14.6M ops)", fontsize=9)
a1.tick_params(labelsize=7)

seeds = ["seed1", "seed2", "seed3"]
x = range(len(seeds))
a2.bar([i - 0.2 for i in x], [M["ir_per_op"][s]["main"] for s in seeds], 0.4, color="#555555", label="main fbabd9df6")
a2.bar([i + 0.2 for i in x], [M["ir_per_op"][s]["fused"] for s in seeds], 0.4, color="#2f6db3", label="fused round")
for i, s in enumerate(seeds):
    a2.text(i + 0.2, M["ir_per_op"][s]["fused"] + 2, f"{M['ir_per_op'][s]['fused']:.1f}", ha="center", fontsize=7)
    a2.text(i - 0.2, M["ir_per_op"][s]["main"] + 2, f"{M['ir_per_op'][s]['main']:.1f}", ha="center", fontsize=7)
a2.set_xticks(list(x))
a2.set_xticklabels([f"{s}\n{M['callgrind_ir_solve'][s]['ops']/1e6:.1f}M ops" for s in seeds])
a2.set_ylim(0, 145)
a2.set_ylabel("Callgrind Ir per group operation", fontsize=8)
a2.set_title("Per seed, identical records", fontsize=9)
a2.legend(fontsize=7, loc="upper center", ncol=2)
a2.tick_params(labelsize=7)

w = M["perfindex_compare_wall"]
ks = ["dlp/c_rho_zp40", "dlp/c_rho_ec36"]
sp = [w[k]["speedup"] for k in ks]
lo = [w[k]["speedup"] - w[k]["ci95"][0] for k in ks]
hi = [w[k]["ci95"][1] - w[k]["speedup"] for k in ks]
a3.bar(ks, sp, color=["#2f6db3", "#9ecae1"], yerr=[lo, hi], capsize=4)
a3.axhline(1.0, color="black", lw=0.8)
for i, s in enumerate(sp):
    a3.text(i, s + 0.04, f"{s:.3f}x", ha="center", fontsize=8)
a3.set_ylim(0.85, 1.35)
a3.set_ylabel("paired wall speedup (95% CI), 7 rounds, CPU 3", fontsize=8)
a3.set_title("perfindex compare (L0, descriptive)", fontsize=9)
a3.tick_params(labelsize=8)
fig.suptitle("cryptanalysis: fused native (Z/pZ)^* rho round, 107.0 -> 67.2 Ir per group operation; every output identical to main", fontsize=9)
fig.tight_layout(rect=(0, 0, 1, 0.92))
for ext, kw in (("svg", {}), ("png", {"dpi": 150})):
    fig.savefig(HERE / "figures" / f"ir_and_wall.{ext}", bbox_inches="tight", **kw)
