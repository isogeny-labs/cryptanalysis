"""Render the retained exact four-summand support counts."""

import json
from pathlib import Path

import matplotlib.pyplot as plt


root = Path(__file__).resolve().parent
data = json.loads((root / "four_sum_mixed_support_results.json").read_text())
rows = data["records"]
labels = [row["arm"] for row in rows]
counts = [row["four_sum_nonidentity_support"] for row in rows]
fig, ax = plt.subplots(figsize=(7.5, 3.0))
ax.barh(range(len(rows)), counts, color=["#5279a5", "#8ba5be", "#db8f45", "#8b9d78", "#8b9d78"])
ax.set_yticks(range(len(rows)), labels)
ax.invert_yaxis()
ax.set_xlim(0, 250)
ax.set_xlabel("Distinct nonidentity four-sums (of 1068 possible targets)")
for i, count in enumerate(counts):
    ax.text(count + 3, i, str(count), va="center")
ax.set_title("Exact support of fixed signed eight-point bases")
fig.tight_layout()
svg_path = root / "four_sum_mixed_support_chart.svg"
fig.savefig(svg_path)
svg_path.write_text("\n".join(line.rstrip() for line in svg_path.read_text().splitlines()) + "\n")
fig.savefig(root / "four_sum_mixed_support_chart.png", dpi=110)
