"""Lay out the recorded values in data/measurements.json (plotting only)."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
M = json.loads((HERE / "data" / "measurements.json").read_text())
(HERE / "figures").mkdir(exist_ok=True)
rows = sorted(M["rows"], key=lambda r: -r["wall_speedup"])
names = [r["id"] for r in rows]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 5.4), sharey=True)
y = list(range(len(rows)))
a1.barh(y, [r["ir_ratio"] for r in rows], color="#2f6db3")
a1.axvline(1.0, color="black", lw=0.8)
for i, r in enumerate(rows):
    a1.text(r["ir_ratio"] + 0.02, i, f"{r['ir_ratio']:.2f}x", va="center", fontsize=7)
a1.set_xlim(0.8, max(r["ir_ratio"] for r in rows) + 0.4)
a1.set_yticks(y)
a1.set_yticklabels(names, fontsize=7)
a1.invert_yaxis()
a1.set_xlabel("Callgrind Ir, main / this change (scalar paths: Valgrind has no AVX-512)", fontsize=7)
a1.set_title("Instructions", fontsize=9)
sp = [r["wall_speedup"] for r in rows]
lo = [max(0.0, r["wall_speedup"] - r["wall_ci95"][0]) for r in rows]
hi = [max(0.0, r["wall_ci95"][1] - r["wall_speedup"]) for r in rows]
a2.barh(y, sp, xerr=[lo, hi], color="#9ecae1", capsize=2)
a2.axvline(1.0, color="black", lw=0.8)
for i, r in enumerate(rows):
    a2.text(0.62, i, f"{r['wall_speedup']:.2f}x", va="center", fontsize=6)
a2.set_xlim(0.6, max(r["wall_ci95"][1] for r in rows) + 0.1)
a2.set_xscale("log")
a2.set_xlabel("paired wall speedup vs main, 95% CI, 7 rounds, CPU 3 (native, AVX-512 on)", fontsize=7)
a2.set_title("Wall (L0, descriptive)", fontsize=9)
fig.suptitle(
    "cryptanalysis suite (Rust): trinomial shift fold, nibble-table inversion chain, shared Gf2 tables, IFMA CSR rows; fingerprints identical",
    fontsize=9,
)
fig.tight_layout(rect=(0, 0, 1, 0.94))
for ext, kw in (("svg", {}), ("png", {"dpi": 150})):
    fig.savefig(HERE / "figures" / f"ir_and_wall.{ext}", bbox_inches="tight", **kw)
