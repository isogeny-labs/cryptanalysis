#!/usr/bin/env python3
"""One-page PDF report for the L2 bench record: decision, table, figure."""
import json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
s = json.load(open("summary.json"))
fig = plt.figure(figsize=(8.27, 11.69))
fig.text(0.06, 0.96, "L2: SBVA preprocessing before CaDiCaL on m = 4 PDP CNFs", fontsize=13, weight="bold")
fig.text(0.06, 0.935, f"Decision (pre-registered rule): {s['decision']}   [pcc:unverified]", fontsize=10)
lines = ["subset: conflicts B/A [95% CI] | A/A [95% CI] | wall B/A [95% CI]"]
f = lambda t: f"{t[0]:.3f} [{t[1]:.3f}, {t[2]:.3f}]"
for k, v in s["cells"].items():
    lines.append(f"{k}: {f(v['rho'])} | {f(v['aa']) if v['aa'] else 'n/a'} | {f(v['omega'])}")
lines += ["", f"rows {s['rows']}, invalid {s['invalid']}, censored {s['censored']}",
          "B = SBVA (git 35e74d0) then CaDiCaL (git 6b3d70b, 3.1.0); A = CaDiCaL alone.",
          "48 base CNFs from crypto dr4.py @ 833a35d (l = 3, 4; plain and dual; 8 UNSAT + 4 SAT targets),",
          "3 seeded shuffles each. Success needed B/A <= 1/1.3 outside the A/A band: not met.",
          "Deviation: 23 arm-A SAT model checks failed because CaDiCaL HEAD omits eliminated",
          "variables from printed models; all 23 re-verified with --elim=0 (model_recheck.json).",
          "Unisolated 4-core shared container; conflicts primary, wall exploratory. Details: RESULT.md."]
fig.text(0.06, 0.62, "\n".join(lines), fontsize=7.5, family="monospace", va="bottom")
fig.text(0.06, 0.58, "Figure: l2_ratios.svg (per-file conflict ratios with A/A), committed alongside.", fontsize=8)
fig.savefig("l2_report.pdf")
