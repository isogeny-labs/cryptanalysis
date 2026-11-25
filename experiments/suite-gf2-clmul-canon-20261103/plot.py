"""Lay out the recorded values in data/measurements.json (plotting only)."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
M = json.loads((HERE / "data" / "measurements.json").read_text())
(HERE / "figures").mkdir(exist_ok=True)
rows = sorted(M["rows"], key=lambda r: -r["ir_ratio"])
names = [r["id"].split("/")[1] for r in rows]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 4.8), sharey=True)
y = range(len(rows))
a1.barh(list(y), [r["ir_ratio"] for r in rows], color="#2f6db3")
a1.axvline(1.0, color="black", lw=0.8)
a1.axvline(2.0, color="#c0392b", ls="--", lw=1)
a1.text(1.98, -0.7, "target 2x", color="#c0392b", fontsize=7, ha="right")
for i, r in enumerate(rows):
    a1.text(r["ir_ratio"] + 0.02, i, f"{r['ir_ratio']:.2f}x", va="center", fontsize=7)
a1.set_xlim(0.8, 2.1)
a1.set_yticks(list(y))
a1.set_yticklabels(names, fontsize=7)
a1.invert_yaxis()
a1.set_xlabel("Callgrind Ir, main / this change (scalar path: Valgrind has no AVX-512)", fontsize=7)
a1.set_title("Instructions", fontsize=9)
sp = [r["wall_speedup"] for r in rows]
lo = [r["wall_speedup"] - r["wall_ci95"][0] for r in rows]
hi = [r["wall_ci95"][1] - r["wall_speedup"] for r in rows]
a2.barh(list(y), sp, xerr=[lo, hi], color="#9ecae1", capsize=2)
a2.axvline(1.0, color="black", lw=0.8)
a2.set_xlim(0.8, 1.25)
a2.set_xlabel("paired wall speedup, 95% CI, 7 rounds, CPU 3 (native, AVX-512 paths on)", fontsize=7)
a2.set_title("Wall (L0, descriptive)", fontsize=9)
fig.suptitle("cryptanalysis suite (Rust): GF(2^n) products inlined through pclmulqdq copies, Frobenius canon; fingerprints identical", fontsize=9)
fig.tight_layout(rect=(0, 0, 1, 0.94))
for ext, kw in (("svg", {}), ("png", {"dpi": 150})):
    fig.savefig(HERE / "figures" / f"ir_and_wall.{ext}", bbox_inches="tight", **kw)
