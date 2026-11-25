#!/usr/bin/env python3
"""One-page PDF report for the L2 bench record: decision, table, figure."""
import json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
s = json.load(open("summary.json"))
fig = plt.figure(figsize=(8.27, 11.69))
fig.text(0.06, 0.96, "L2c: confirmatory RREF effect on decomposable PDP targets", fontsize=13, weight="bold")
fig.text(0.06, 0.935, f"Decision (pre-registered rule): {s['decision']}   [pcc:unverified]", fontsize=10)
lines = ["subset: conflicts C/A [95% CI] | A/A [95% CI] | wall C/A [95% CI]"]
f = lambda t: f"{t[0]:.3f} [{t[1]:.3f}, {t[2]:.3f}]"
for k, v in s["cells"].items():
    lines.append(f"{k}: {f(v['rho'])} | {f(v['aa']) if v['aa'] else 'n/a'} | {f(v['omega'])}")
lines += ["", f"rows {s['rows']}, invalid {s['invalid']}, censored {s['censored']}",
          "C = CaDiCaL (6b3d70b) on base + RREF prefix chains; A = base. Fresh curve, 16 planted targets per cell.",
          "64 base CNFs, dr4.py @ 833a35d, seed base 2026111800 (l = 3, 4; plain, dual),",
          "3 shuffles each. CONFIRMED needs GM <= 0.769, upper < 1, no A/A overlap: met.",
          "Scope: solver-behaviour finding on SAT instances; break-even decomposable fraction",
          "about 0.22 using L2b UNSAT cost (1.061x), so no net gain at typical m = 4 yields.",
          "Unisolated 4-core shared container; conflicts primary, wall exploratory. Details: RESULT.md."]
fig.text(0.06, 0.62, "\n".join(lines), fontsize=7.5, family="monospace", va="bottom")
fig.text(0.06, 0.58, "Figure: l2c_ratios.svg (per-file conflict ratios with A/A), committed alongside.", fontsize=8)
fig.savefig("l2c_report.pdf")
