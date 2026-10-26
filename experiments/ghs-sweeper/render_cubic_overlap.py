"""Render the historical evidence supplement; no field or curve computation."""
import csv
import json
import os
from pathlib import Path
import subprocess
import tempfile

cache = Path(tempfile.gettempdir()) / "ghs-overlap-render-cache"
cache.mkdir(exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(cache))
os.environ.setdefault("MPLCONFIGDIR", str(cache / "matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parent
fig = root / "cubic-gluing-figures"
data = json.loads((root / "cubic-gluing-checks/five-only-historical-overlap.json").read_text())
rows = data["rows"]
with (fig / "historical-overlap.csv").open("w", newline="") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["source_trace", "verified_historical_cover_models"])
    writer.writerows((r["trace"], r["verified_historical_matches"]) for r in rows)
plt.rcParams.update({"font.size": 10, "svg.fonttype": "none"})
chart, ax = plt.subplots(figsize=(8.5, 2.8), layout="constrained")
ax.bar(range(len(rows)), [r["verified_historical_matches"] for r in rows], color="#71636d")
ax.set_xticks(range(len(rows)), [str(r["trace"]) for r in rows])
ax.set_ylabel("Historical cover-model rows")
ax.set_xlabel("Selected source trace over F512")
ax.set_title("All 12 selected source trace classes already occur in history")
for suffix in ("pdf", "svg"):
    chart.savefig(fig / f"historical-overlap.{suffix}")
    subprocess.run(["dot", f"-T{suffix}", str(fig / "overlap-scope.dot"),
                    "-o", str(fig / f"overlap-scope.{suffix}")], check=True)
plt.close(chart)
subprocess.run(["pandoc", str(root / "CUBIC_PRIOR_OVERLAP.md"), "--from=markdown",
                "--pdf-engine=xelatex", "--resource-path=" + str(root),
                "-o", str(root / "CUBIC_PRIOR_OVERLAP.pdf")], cwd=root, check=True)
