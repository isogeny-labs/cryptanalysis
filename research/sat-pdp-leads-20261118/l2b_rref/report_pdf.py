#!/usr/bin/env python3
"""One-page PDF report for the L2 bench record: decision, table, figure."""
import json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
s = json.load(open("summary.json"))
fig = plt.figure(figsize=(8.27, 11.69))
fig.text(0.06, 0.96, "L2b: RREF XOR prefix-chain extension variables for CaDiCaL", fontsize=13, weight="bold")
fig.text(0.06, 0.935, f"Decision (pre-registered rule): {s['decision']}   [pcc:unverified]", fontsize=10)
lines = ["subset: conflicts C/A [95% CI] | A/A [95% CI] | wall C/A [95% CI]"]
f = lambda t: f"{t[0]:.3f} [{t[1]:.3f}, {t[2]:.3f}]"
for k, v in s["cells"].items():
    lines.append(f"{k}: {f(v['rho'])} | {f(v['aa']) if v['aa'] else 'n/a'} | {f(v['omega'])}")
lines += ["", f"rows {s['rows']}, invalid {s['invalid']}, censored {s['censored']}",
          "C = CaDiCaL (git 6b3d70b) on base CNF + RREF rows as prefix chains; A = same on base CNF.",
          "48 base CNFs from crypto dr4.py @ 833a35d (l = 3, 4; plain and dual; 8 UNSAT + 4 SAT targets),",
          "3 seeded shuffles each. Success needed B/A <= 1/1.3 outside the A/A band: not met.",
          "Incomplete printed models re-verified in-run with --elim=0 (49 SAT answers, all ok).",
          "Arm A identical to L2 arm A on 144/144 pairs. Exploratory: l4 SAT C/A = 0.358 (not deciding).",
          "Unisolated 4-core shared container; conflicts primary, wall exploratory. Details: RESULT.md."]
fig.text(0.06, 0.62, "\n".join(lines), fontsize=7.5, family="monospace", va="bottom")
fig.text(0.06, 0.58, "Figure: l2b_ratios.svg (per-file conflict ratios with A/A), committed alongside.", fontsize=8)
fig.savefig("l2b_report.pdf")
