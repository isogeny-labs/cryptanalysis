"""Render the native data only; no field, matrix, solver or statistic is computed."""
from pathlib import Path
import hashlib
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import typst

p = Path(__file__).resolve().parent
source = p / "native-observations.json"
rows = json.loads(source.read_text())["observations"]
plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none", "font.size": 9})
fig, ax = plt.subplots(figsize=(10.6, 6.5), layout="constrained")
positions = list(range(len(rows)))
ax.barh([i - 0.19 for i in positions], [r["full_nullity"] for r in rows], height=0.34, label="Full kernel nullity", color="#3e6f9f")
ax.barh([i + 0.19 for i in positions], [r["projected_dimension"] for r in rows], height=0.34, label="Projection dimension", color="#43875d")
ax.set_yticks(positions, [r["name"].replace("_", " ") for r in rows])
ax.invert_yaxis()
ax.set_xlim(0, 6.7)
ax.set_xticks(range(7))
ax.set_xlabel("Dimension over F101 (synthetic fixtures)")
ax.set_title("Full nullity includes LP nuisance directions", loc="left", weight="bold")
ax.grid(axis="x", alpha=0.2)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.legend(loc="lower right", frameon=False)
fig.savefig(p / "synthetic-projection-dimensions.svg")
plt.close(fig)
typst.compile(str(p / "report.typ"), output=str(p / "report.pdf"), root=str(p))
(p / "render-receipt.json").write_text(json.dumps({
    "native_input_bytes": source.stat().st_size,
    "native_input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "matplotlib": matplotlib.__version__,
    "scope": "rendering only; native data and native table generation retained separately",
    "PDF_bytes": (p / "report.pdf").stat().st_size,
    "PDF_sha256": hashlib.sha256((p / "report.pdf").read_bytes()).hexdigest(),
}, indent=2) + "\n")
