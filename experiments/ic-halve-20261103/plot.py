"""Lay out the recorded values in data/measurements.json (plotting only)."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
M = json.loads((HERE / "data" / "measurements.json").read_text())
(HERE / "figures").mkdir(exist_ok=True)
ir = {k.split("/")[1]: v for k, v in M["perfindex_instr"].items() if k.startswith("relation/")}
ir["ca ic lsieve p52 (whole)"] = [M["ca_ic_lsieve_p52"]["main_ir"], M["ca_ic_lsieve_p52"]["new_ir"]]
names = list(ir)
ratio = [ir[n][0] / ir[n][1] for n in names]
w = {k.split("/")[1]: v for k, v in M["perfindex_compare_wall_relation"].items() if k.startswith("relation/")}
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.2))
cols = ["#2f6db3" if r >= 2 else "#9ecae1" for r in ratio]
a1.barh(names, ratio, color=cols)
a1.axvline(2.0, color="#c0392b", ls="--", lw=1)
a1.text(2.02, len(names) - 0.6, "target 2x", color="#c0392b", fontsize=7)
for i, r in enumerate(ratio):
    a1.text(r + 0.04, i, f"{r:.2f}x", va="center", fontsize=8)
a1.set_xlim(0, 3.4)
a1.set_xlabel("Callgrind instructions, main / this change", fontsize=8)
a1.set_title("Instructions (deterministic)", fontsize=9)
a1.tick_params(labelsize=8)
wn = list(w)
sp = [w[n]["speedup"] for n in wn]
lo = [w[n]["speedup"] - w[n]["ci95"][0] for n in wn]
hi = [w[n]["ci95"][1] - w[n]["speedup"] for n in wn]
a2.barh(wn, sp, xerr=[lo, hi], color="#2f6db3", capsize=3)
a2.axvline(1.0, color="black", lw=0.8)
a2.set_xscale("log")
for i, s in enumerate(sp):
    a2.text(s * 1.08, i, f"{s:.2f}x", va="center", fontsize=8)
a2.set_xlim(0.9, 14)
a2.set_xlabel("paired wall speedup, 95% CI, 7 rounds, CPU 3 (log)", fontsize=8)
a2.set_title("Wall (L0, descriptive)", fontsize=9)
a2.tick_params(labelsize=8)
fig.suptitle("cryptanalysis index calculus: Lanczos kernels, smoothness test and dense solve; every output identical to main", fontsize=9)
fig.tight_layout(rect=(0, 0, 1, 0.93))
for ext, kw in (("svg", {}), ("png", {"dpi": 150})):
    fig.savefig(HERE / "figures" / f"ic_ir_and_wall.{ext}", bbox_inches="tight", **kw)
