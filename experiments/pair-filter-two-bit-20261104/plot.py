"""Wall ratios from data/filter-compare.json and data/penta-fold-compare.json (plotting only)."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
(HERE / "figures").mkdir(exist_ok=True)
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
for ax, name, title, color in (
    (axes[0], "filter-compare.json", "Two-bit presence filter (adopted)", "#2f6db3"),
    (axes[1], "penta-fold-compare.json", "Pentanomial shift fold (dropped)", "#c0392b"),
):
    ks = json.loads((HERE / "data" / name).read_text())["kernels"]
    if name.startswith("penta"):
        keep = (
            "gf2_n53_mul_sqr_1m",
            "gf2_n53_inv_16k",
            "gf2_n53_batch_inv_4x64k",
            "koblitz_n53_add_many_lazy_64x2k",
            "koblitz_collect_k0n53_w477_u1024",
            "koblitz_descent_k0n53_m2_x4",
        )
        ks = [k for k in ks if k["id"].split("/")[1] in keep]
    ks.sort(key=lambda k: -k["speedup"])
    y = range(len(ks))
    sp = [k["speedup"] for k in ks]
    lo = [max(0.0, k["speedup"] - k["speedup_ci95"][0]) for k in ks]
    hi = [max(0.0, k["speedup_ci95"][1] - k["speedup"]) for k in ks]
    ax.barh(list(y), sp, xerr=[lo, hi], color=color, alpha=0.8, capsize=2)
    ax.axvline(1, color="black", lw=0.8)
    for j, k in enumerate(ks):
        ax.text(0.52, j, f"{k['speedup']:.3f}x", va="center", fontsize=6)
    ax.set_yticks(list(y), [k["id"].split("/")[1] for k in ks], fontsize=6)
    ax.invert_yaxis()
    ax.set_xlim(0.5, 1.8)
    ax.set_xlabel("paired wall speedup vs main, 95% CI (L0, CPU 3)", fontsize=7)
    ax.set_title(title, fontsize=9)
fig.suptitle("Folded pair-table filter and GF(2^53) reduction, on a host without VPCLMULQDQ", fontsize=9)
fig.tight_layout(rect=(0, 0, 1, 0.93))
for ext, kw in (("svg", {}), ("png", {"dpi": 150})):
    fig.savefig(HERE / "figures" / f"wall.{ext}", bbox_inches="tight", **kw)
