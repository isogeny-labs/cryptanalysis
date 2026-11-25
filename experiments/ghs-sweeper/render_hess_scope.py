"""Render the algebraic report; this is documentation tooling, not the sweeper."""
from pathlib import Path
import csv
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "scope-figures"
FIG.mkdir(exist_ok=True)

for suffix in ("svg", "pdf"):
    subprocess.run(["dot", f"-T{suffix}", str(FIG / "inclusion.dot"),
                    "-o", str(FIG / f"inclusion.{suffix}")], check=True)

values = [(n, (1 << n) - 2) for n in range(2, 14)]
with (FIG / "genus-bound.csv").open("w", newline="") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["relative_degree_N", "derived_existence_genus_upper_bound"])
    writer.writerows(values)

fig, ax = plt.subplots(figsize=(7.0, 3.3), constrained_layout=True)
ax.plot(*zip(*values), marker="o", color="#365d7d", linewidth=1.7, markersize=4)
ax.set_yscale("log", base=2)
ax.set_xticks(range(2, 14))
ax.set_xlabel("Relative extension degree N")
ax.set_ylabel("Existence upper bound on genus")
ax.set_title("Published Hess construction: bound 2^N - 2", fontsize=11)
ax.grid(True, alpha=0.22)
fig.text(0.5, -0.04,
         "Exact formula at 12 integer arguments; neither an optimized genus nor a cost measurement.",
         ha="center", fontsize=8)
for suffix in ("svg", "pdf"):
    fig.savefig(FIG / f"genus-bound.{suffix}", bbox_inches="tight")
plt.close(fig)

subprocess.run([
    "pandoc", str(ROOT / "HESS_SCOPE.md"), "--from=markdown", "--pdf-engine=xelatex",
    "--resource-path=" + str(ROOT), "-o", str(ROOT / "HESS_SCOPE.pdf"),
], cwd=ROOT, check=True)
