"""Render frozen census evidence and written proof; no curve computations."""
import csv
import json
import os
from pathlib import Path
import subprocess
import tempfile

cache = Path(tempfile.gettempdir()) / "ghs-quartic-render-cache"
cache.mkdir(exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(cache))
os.environ.setdefault("MPLCONFIGDIR", str(cache / "matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parent
fig = root / "quartic-cubic-figures"
data = json.loads((root / "quartic-cubic-checks/census-attempt-1.json").read_text())
labels = ["All vectors", "Smooth", "C3 reps", "N1=9", "Also N2=65", "t=-35", "t=+35"]
counts = [data[k] for k in ["parameter_vectors", "smooth_vectors", "smooth_c3_orbit_representatives", "N1_9_representatives", "N1_9_N2_65_representatives"]]
counts += [sum(r["source_trace"] == t for r in data["target_representatives"]) for t in [-35, 35]]
with (fig / "census.csv").open("w", newline="") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["stage", "exact_count"])
    writer.writerows(zip(labels, counts))
plt.rcParams.update({"font.size": 9, "svg.fonttype": "none", "pdf.use14corefonts": True})
chart, ax = plt.subplots(figsize=(8, 2.7), layout="constrained")
ax.bar(labels, counts, color=["#667c90"] * 5 + ["#43845c", "#43845c"])
ax.set_yscale("log")
ax.set_ylim(1, 1500000)
ax.set_ylabel("Exact number (log scale)")
ax.set_title("Complete published O3 parameter census over F8")
for i, value in enumerate(counts):
    ax.text(i, value * 1.17, f"{value:,}", ha="center", va="bottom", fontsize=8)
for suffix in ["pdf", "svg"]:
    chart.savefig(fig / f"census.{suffix}")
    subprocess.run(["dot", f"-T{suffix}", str(fig / "transfer-scope.dot"), "-o", str(fig / f"transfer-scope.{suffix}")], check=True)
plt.close(chart)
for name in ["QUARTIC_CUBIC_RESULTS", "CUBIC_CM_DISCRIMINANT"]:
    subprocess.run(["pandoc", str(root / f"{name}.md"), "--from=markdown", "--pdf-engine=xelatex", "-V", "monofont=Latin Modern Roman", "--resource-path=" + str(root), "-o", str(root / f"{name}.pdf")], cwd=root, check=True)
