"""Figure from data/perfindex-instr.json and data/perfindex-compare-15r.json (plotting only)."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
ir = {k["id"]: k for k in json.loads((HERE / "data/perfindex-instr.json").read_text())["kernels"]}
wall = {k["id"]: k for k in json.loads((HERE / "data/perfindex-compare-15r.json").read_text())["kernels"]}
ids = sorted(ir, key=lambda i: -ir[i]["speedup"])
(HERE / "figures").mkdir(exist_ok=True)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.6), gridspec_kw={"width_ratios": [3, 2]})
y = range(len(ids))
a1.barh(list(y), [ir[i]["speedup"] for i in ids], color="#2f6db3")
for j, i in enumerate(ids):
    a1.text(ir[i]["speedup"] + 0.01, j, f"{ir[i]['speedup']:.3f}x", va="center", fontsize=7)
a1.axvline(1, color="black", lw=0.8)
a1.set_yticks(list(y), [i.split("/")[1] for i in ids], fontsize=7)
a1.invert_yaxis()
a1.set_xlim(0.9, 1.4)
a1.set_xlabel("Callgrind Ir, main / this change (fingerprints identical)", fontsize=7)
a1.set_title("Instructions", fontsize=9)
w = list(wall)
sp = [wall[i]["speedup"] for i in w]
lo = [wall[i]["speedup"] - wall[i]["speedup_ci95"][0] for i in w]
hi = [wall[i]["speedup_ci95"][1] - wall[i]["speedup"] for i in w]
a2.barh(range(len(w)), sp, xerr=[lo, hi], color="#9ecae1", capsize=3)
a2.axvline(1, color="black", lw=0.8)
a2.set_yticks(range(len(w)), [i.split("/")[1] for i in w], fontsize=7)
a2.set_xlabel("paired wall speedup, 95% CI, 15 rounds, CPU 3 (L0)", fontsize=7)
a2.set_title("Wall (descriptive)", fontsize=9)
fig.suptitle("Cofactor projection of the factor base: one product per Frobenius orbit", fontsize=9)
fig.tight_layout(rect=(0, 0, 1, 0.93))
for ext, kw in (("svg", {}), ("png", {"dpi": 150})):
    fig.savefig(HERE / "figures" / f"proj.{ext}", bbox_inches="tight", **kw)
