"""Render recorded exact agreement rates; does no research computation."""

import json
from pathlib import Path

import matplotlib.pyplot as plt


root = Path(__file__).resolve().parent
data = json.loads((root / "isogeny_derivative_character_results.json").read_text())
rows = [(f"p={case['p']}  ell={edge['degree']}  edge={edge['edge_index']}",
         edge["matches_best_global_sign"], edge["tested_nonzero_points"])
        for case in data["cases"] for edge in case["edges"]]
fig, ax = plt.subplots(figsize=(8.4, 3.6))
rates = [matches / total for _, matches, total in rows]
ax.barh(range(len(rows)), rates, color="#5279a5")
ax.set_yticks(range(len(rows)), [name for name, _, _ in rows])
ax.invert_yaxis()
ax.set_xlim(0, 1.05)
ax.set_xlabel("Best global-sign agreement / all nonzero scalars (exact census)")
ax.axvline(1, color="#ae4b4b", linestyle="--", linewidth=1, label="exact identity")
for i, (_, matches, total) in enumerate(rows):
    ax.text(rates[i] + 0.015, i, f"{matches}/{total}", va="center", fontsize=9)
ax.set_title("Isogeny derivative vs scalar quadratic character")
ax.legend(loc="lower right")
fig.tight_layout()
svg_path = root / "isogeny_derivative_character_agreement.svg"
fig.savefig(svg_path)
svg_path.write_text("\n".join(line.rstrip() for line in svg_path.read_text().splitlines()) + "\n")
fig.savefig(root / "isogeny_derivative_character_agreement.png", dpi=110)
