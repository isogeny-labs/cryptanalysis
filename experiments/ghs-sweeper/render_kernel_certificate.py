"""Render documentation from retained Rust output; no curve search runs here."""
from pathlib import Path
import csv
import json
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "kernel-figures"
OUT = ROOT / "kernel-checks"
for suffix in ("svg", "pdf"):
    subprocess.run(["dot", f"-T{suffix}", str(FIG / "certificate.dot"),
                    "-o", str(FIG / f"certificate.{suffix}")], check=True)

positive = json.loads((OUT / "certificate-a0.json").read_text())["checks"]
controls = {"Mixed kernel": positive}
for line in (OUT / "all-targets-attempt-2.txt").read_text().splitlines():
    if line.startswith("negative_control "):
        _, name, payload = line.split(" ", 2)
        controls[{"decomposable": "Decomposable", "nonisotropic": "Nonisotropic"}[name]] = json.loads(payload)
assert len(controls) == 3
rows = [(name, row["ordered_pairings_evaluated"], row["nontrivial_product_pairings"],
         max(row["coordinate_intersection_sizes"]), row["frobenius_stable"], row["accepted"])
        for name, row in controls.items()]
with (FIG / "control-checks.csv").open("w", newline="") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["fixed_subgroup", "ordered_pairs", "nontrivial_product_pairings",
                     "largest_coordinate_intersection", "frobenius_stable", "accepted"])
    writer.writerows(rows)

fig, axes = plt.subplots(1, 2, figsize=(8, 2.7), constrained_layout=True)
names = [row[0] for row in rows]
colors = ["#3b6b88", "#b78c43", "#9a4c48"]
for ax, column, title, ylabel in [(axes[0], 2, "Pairing predicate", "Nontrivial pairs / 729"),
                                  (axes[1], 3, "Coordinate intersection", "Points, including identity")]:
    values = [row[column] for row in rows]
    ax.bar(names, values, color=colors)
    ax.set_title(title, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.tick_params(axis="x", labelrotation=18, labelsize=8)
    for i, value in enumerate(values):
        ax.annotate(str(value), (i, value), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=9)
    ax.set_ylim(0, max(values) * 1.23)
    ax.grid(axis="y", alpha=0.2)
axes[1].axhline(1, color="#45627c", linestyle="--", linewidth=0.8)
for suffix in ("svg", "pdf"):
    fig.savefig(FIG / f"control-checks.{suffix}")
plt.close(fig)
subprocess.run([
    "pandoc", str(ROOT / "KERNEL_CERTIFICATE.md"), "--from=markdown",
    "--pdf-engine=xelatex", "--resource-path=" + str(ROOT),
    "-o", str(ROOT / "KERNEL_CERTIFICATE.pdf"),
], cwd=ROOT, check=True)
