"""Lay out the recorded values in data/measurements.json: Callgrind Ir per
group operation for each variant, and the interleaved wall rounds of the
kept variant against the baseline (with the baseline-against-itself arm).
Plotting only; the quotient Ir/ops is the only arithmetic, and it is in
measurements.json too."""

import json
import statistics as st
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / (sys.argv[1] if len(sys.argv) > 1 else "figures")
OUT.mkdir(parents=True, exist_ok=True)
M = json.loads((HERE / "data" / "measurements.json").read_text())

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.3), gridspec_kw={"width_ratios": [1.25, 1]})
names = list(M["ir_per_op"])
vals = [M["ir_per_op"][n] for n in names]
colors = ["#555555", "#9ecae1", "#9ecae1", "#9ecae1", "#9ecae1", "#d9d9d9", "#2f6db3"]
hatch = ["", "", "", "", "", "//", ""]
ax1.barh(range(len(names)), vals, color=colors, hatch=hatch, edgecolor="#777777", linewidth=0.4)
for i, v in enumerate(vals):
    ax1.text(v + 2, i, f"{v:.1f}", va="center", fontsize=8)
ax1.set_yticks(range(len(names)))
ax1.set_yticklabels([n.replace(" (main 8a93e468d)", "\n(main 8a93e468d)").replace(", ec_batch_op", ",\nec_batch_op").replace(" (negation", "\n(negation").replace(" (rejected)", "\n(rejected)") for n in names], fontsize=6.8)
ax1.invert_yaxis()
ax1.set_xlim(0, max(vals) * 1.18)
ax1.set_xlabel("Callgrind Ir per group operation (deterministic; 4,907,163 operations, seed 1)", fontsize=7.5)
ax1.set_title("Instructions per rho step, 44-bit prime-order curve", fontsize=9)

rows = M["wall_seconds_internal"]["final_rounds"] if "final_rounds" in M["wall_seconds_internal"] else M["wall_seconds_internal"]["v3_rounds"]
a = [float(r[1]) for r in rows]
b = [float(r[2]) for r in rows]
c = [float(r[3]) for r in rows]
x = range(1, len(rows) + 1)
ax2.plot(x, a, "o-", color="#555555", label=f"baseline (median {st.median(a):.3f} s)")
ax2.plot(x, b, "s-", color="#2f6db3", label=f"kept variant (median {st.median(b):.3f} s)")
ax2.plot(x, c, "^--", color="#999999", label=f"baseline again, A/A (median {st.median(c):.3f} s)")
ax2.set_xlabel("interleaved round (baseline, candidate, baseline; CPU 3 pinned; L0 shared VM)", fontsize=7.5)
ax2.set_ylabel("solver-reported seconds, one thread", fontsize=8)
ax2.set_ylim(0, max(a + b + c) * 1.25)
ax2.legend(fontsize=7, frameon=False, loc="lower right")
ax2.set_title("Wall time of the same solve (descriptive, not isolated)", fontsize=9)
ax2.tick_params(labelsize=8)
fig.suptitle("cryptanalysis: the EC rho step rewritten with inline arithmetic and four interleaved inversion chains; "
             "every output identical to main", fontsize=9)
fig.tight_layout(rect=(0, 0, 1, 0.94))
for ext, kw in (("svg", {}), ("png", {"dpi": 150})):
    fig.savefig(OUT / f"ir_and_wall.{ext}", bbox_inches="tight", **kw)
