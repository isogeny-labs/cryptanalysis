"""Lay out the recorded values in data/measurements.json (plotting only)."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
M = json.loads((HERE / "data" / "measurements.json").read_text())
(HERE / "figures").mkdir(exist_ok=True)
fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(12, 3.8))
for ax, (title, vals, unit) in zip(
    (a1, a2),
    [
        ("Whole Z_p rho solve, seed 2 (14.6M ops)", M["ir_per_op_seed2"], "Callgrind Ir per group operation"),
        ("perfindex dlp/c_rho_zp40", {k: v for k, v in zip(["main 0045cfa09", "native Z_p step"], M["perfindex_instr"]["dlp/c_rho_zp40"])}, "Callgrind Ir"),
    ],
):
    names = list(vals)
    v = [vals[n] for n in names]
    ax.bar(names, v, color=["#555555", "#2f6db3"])
    for i, x in enumerate(v):
        ax.text(i, x * 1.01, f"{x:,.1f}" if x < 1000 else f"{x/1e6:.1f}M", ha="center", fontsize=8)
    ax.set_ylabel(unit, fontsize=8)
    ax.set_title(title, fontsize=9)
    ax.set_ylim(0, max(v) * 1.15)
    ax.tick_params(labelsize=8)
w = M["perfindex_compare_wall"]
ks = ["dlp/c_rho_zp40", "dlp/c_rho_ec36"]
sp = [w[k]["speedup"] for k in ks]
lo = [w[k]["speedup"] - w[k]["ci95"][0] for k in ks]
hi = [w[k]["ci95"][1] - w[k]["speedup"] for k in ks]
a3.bar(ks, sp, color=["#2f6db3", "#9ecae1"], yerr=[lo, hi], capsize=4)
a3.axhline(1.0, color="black", lw=0.8)
for i, x in enumerate(sp):
    a3.text(i, x + 0.03, f"{x:.3f}x", ha="center", fontsize=8)
a3.set_ylim(0.9, 1.25)
a3.set_ylabel("paired wall speedup (95% CI), 7 rounds, CPU 3", fontsize=8)
a3.set_title("perfindex compare (L0, descriptive)", fontsize=9)
a3.tick_params(labelsize=8)
fig.suptitle("cryptanalysis: the native (Z/pZ)^* rho step inline; every output identical to main", fontsize=9)
fig.tight_layout(rect=(0, 0, 1, 0.92))
for ext, kw in (("svg", {}), ("png", {"dpi": 150})):
    fig.savefig(HERE / "figures" / f"ir_and_wall.{ext}", bbox_inches="tight", **kw)
