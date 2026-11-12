"""Render recorded acceptance/control counts; no research computation."""
from pathlib import Path
import json
import subprocess
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import typst
p=Path(__file__).resolve().parent
subprocess.run(["dot","-Tsvg",str(p/"replay.dot"),"-o",str(p/"replay.svg")],check=True)
rows=json.loads((p/"counts.json").read_text())["rows"]
plt.rcParams.update({"svg.fonttype":"none","font.family":"DejaVu Sans","font.size":9})
fig,ax=plt.subplots(figsize=(7.5,1.6),layout="constrained")
bars=ax.barh([r["name"] for r in rows],[r["rejected"] for r in rows],color="#4f8b6b")
ax.bar_label(bars,labels=[str(r["rejected"])+" / "+str(r["total"]) for r in rows],padding=4)
ax.set_xlim(0,7.5);ax.set_xticks(range(8));ax.set_xlabel("Rejected inputs / all preregistered mutants · checker02 /163fbf")
ax.spines[["top","right"]].set_visible(False)
fig.savefig(p/"counts.svg");plt.close(fig)
for f in p.glob("*.svg"):f.write_text("\n".join(x.rstrip() for x in f.read_text().splitlines()).rstrip()+"\n")
typst.compile(str(p/"report.typ"),output=str(p/"report.pdf"))
