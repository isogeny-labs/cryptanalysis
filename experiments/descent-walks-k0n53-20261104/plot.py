"""Figure from data/analysis.json and data/ir-per-trial.json (plotting only)."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
A = json.loads((HERE / "data" / "analysis.json").read_text())
IR = json.loads((HERE / "data" / "ir-per-trial.json").read_text())
(HERE / "figures").mkdir(exist_ok=True)
fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(13, 4.2))
arms = ["W128", "W256", "W512"]
x = range(len(arms))
rho = [A["arms"][a]["rho"] for a in arms]
lo = [A["arms"][a]["rho"] - A["arms"][a]["rho_ci95"][0] for a in arms]
hi = [A["arms"][a]["rho_ci95"][1] - A["arms"][a]["rho"] for a in arms]
a1.bar(x, rho, yerr=[lo, hi], color="#2f6db3", capsize=4)
a1.axhspan(1 - A["h_aa"], 1 + A["h_aa"], color="#bbbbbb", alpha=0.5, label=f"A/A noise ±{100*A['h_aa']:.1f}%")
a1.axhline(1, color="black", lw=0.8)
for i, v in enumerate(rho):
    a1.text(i + 0.06, A["arms"][arms[i]]["rho_ci95"][1] + 0.004, f"{v:.3f}x", ha="left", fontsize=8)
a1.set_xticks(list(x), arms)
a1.set_ylim(0.95, 1.15)
a1.set_ylabel("cost per trial, W64 / arm (95% CI)")
a1.set_title("Primary: wall per trial (native)", fontsize=9)
a1.legend(fontsize=7, loc="upper left")
pd = [A["arms"][a]["per_descent_ratio"] for a in arms]
pl = [A["arms"][a]["per_descent_ratio"] - A["arms"][a]["per_descent_ci95"][0] for a in arms]
ph = [A["arms"][a]["per_descent_ci95"][1] - A["arms"][a]["per_descent_ratio"] for a in arms]
tr = [A["arms"][a]["trials_ratio"] for a in arms]
tl = [A["arms"][a]["trials_ratio"] - A["arms"][a]["trials_ci95"][0] for a in arms]
th = [A["arms"][a]["trials_ci95"][1] - A["arms"][a]["trials_ratio"] for a in arms]
a2.errorbar([i - 0.1 for i in x], pd, yerr=[pl, ph], fmt="o", label="wall per descent, W64 / arm", color="#2f6db3", capsize=3)
a2.errorbar([i + 0.1 for i in x], tr, yerr=[tl, th], fmt="s", label="mean trials, arm / W64", color="#c0392b", capsize=3)
a2.axhline(1, color="black", lw=0.8)
a2.set_xticks(list(x), arms)
a2.set_title("Secondary: per descent, and trial check", fontsize=9)
a2.legend(fontsize=7)
ws = ["64", "128", "256", "512"]
a3.bar(range(4), [IR[w]["ir_per_trial"] for w in ws], color="#9ecae1")
for i, w in enumerate(ws):
    a3.text(i, IR[w]["ir_per_trial"] + 5, f"{IR[w]['ir_per_trial']:.0f}", ha="center", fontsize=8)
a3.set_xticks(range(4), [f"W{w}" for w in ws])
a3.set_ylim(600, 760)
a3.set_ylabel("Callgrind Ir per trial (scalar path)")
a3.set_title("Secondary: instructions, 8 targets", fontsize=9)
fig.suptitle("k0n53 walked descent: walks per shared inversion (256 held-out targets x 3 rounds, all logs verified)", fontsize=9)
fig.tight_layout(rect=(0, 0, 1, 0.93))
for ext, kw in (("svg", {}), ("png", {"dpi": 150})):
    fig.savefig(HERE / "figures" / f"walks.{ext}", bbox_inches="tight", **kw)
