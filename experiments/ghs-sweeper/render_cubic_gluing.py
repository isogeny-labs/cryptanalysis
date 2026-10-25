"""Documentation only; all source and module computations are native Rust."""
import csv
import json
import os
from pathlib import Path
import subprocess
import tempfile

cache = Path(tempfile.gettempdir()) / "ghs-cubic-render-cache"
cache.mkdir(exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(cache))
os.environ.setdefault("MPLCONFIGDIR", str(cache / "matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parent
fig = root / "cubic-gluing-figures"
source = json.loads((root / "cubic-gluing-checks/binary-census-attempt-1.json").read_text())
rows = [r for r in source["rows"] if r["five_module_status"] == "split_distinct" and not r["three_kernel"]]
with (fig / "source-traces.csv").open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(["source_trace", "exact_source_models"])
    writer.writerows((r["trace"], r["models"]) for r in rows)
plt.rcParams.update({"font.size": 10, "svg.fonttype": "none"})
chart, ax = plt.subplots(figsize=(8.5, 3.2), layout="constrained")
ax.bar(range(len(rows)), [r["models"] for r in rows], color="#176b87")
ax.set_xticks(range(len(rows)), [str(r["trace"]) for r in rows])
ax.set_xlabel("Exact K-trace, K = F512")
ax.set_ylabel("Source models (count)")
ax.set_title("Five-kernel positive, three-kernel negative: 252 of 1,008 models")
ax.set_yticks([0, 9, 18, 27])
ax.set_ylim(0, 30)
for i, row in enumerate(rows):
    ax.text(i, row["models"] + 0.5, str(row["models"]), ha="center", fontsize=9)
for suffix in ("svg", "pdf"):
    chart.savefig(fig / f"source-traces.{suffix}")
    for name in ("criterion", "five-geometry"):
        subprocess.run(["dot", f"-T{suffix}", str(fig / f"{name}.dot"),
                        "-o", str(fig / f"{name}.{suffix}")], check=True)
plt.close(chart)
for name in ("CUBIC_GLUING", "FIVE_GLUING_GEOMETRY", "CUBIC_GLUING_RESULTS"):
    subprocess.run(["pandoc", str(root / f"{name}.md"), "--from=markdown",
                    "--pdf-engine=xelatex", "--resource-path=" + str(root),
                    "-o", str(root / f"{name}.pdf")], cwd=root, check=True)
