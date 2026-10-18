"""Plot recorded native receipts only; performs no cryptographic computation."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

here = Path(__file__).resolve().parent
data = json.loads((here / "run1-summary.json").read_text())
local = data["additive_local_ingestion"]
frontier = data["frontier"]
fig, (left, right) = plt.subplots(1, 2, figsize=(10.8, 3.8), gridspec_kw={"width_ratios": [1.15, 1]})
labels = ["All report metadata", "Zero trails replayed", "Positive trails replayed", "Positive trails unreplayed"]
counts = [local["independent_curve_weight_seed_encoding_checks"], local["zero_length_golden_replayed"],
          local["positive_trails_replayed"], local["trails_not_replayed"]]
bars = left.barh(labels, counts, color=["#477d64", "#477d64", "#477d64", "#c18b42"])
left.set_xscale("log")
left.set_xlim(1, 6500)
left.invert_yaxis()
for bar, count in zip(bars, counts):
    left.text(count*1.12, bar.get_y()+bar.get_height()/2, f"{count:,}", va="center", fontsize=9)
left.set_xlabel("Reports (log scale; metadata total overlaps trail groups)", fontsize=8)
left.set_title("Additive local v2 qualification", fontsize=11)
memory = [frontier["peak_rss_bytes"] / 1e9,
          frontier["memory_gate"]["process_address_space_cap_bytes"] / 1e9,
          frontier["memory_gate"]["effective_limit_bytes"] / 1e9]
bars = right.bar(["Peak RSS\nmeasured", "Address-space\npolicy cap", "Host/cgroup\neffective cap"], memory,
                 color=["#b95b58", "#c18b42", "#75859c"])
bars[0].set_hatch("//")
for bar, count in zip(bars, memory):
    right.text(bar.get_x()+bar.get_width()/2, count+2, f"{count:.2f}", ha="center", fontsize=9)
right.set_ylim(0, 145)
right.set_ylabel("Decimal GB (resident and virtual limits are distinct)", fontsize=8)
right.set_title("Original CPU closure: allocation failure", fontsize=11)
for axis in (left, right):
    axis.spines[["top", "right"]].set_visible(False)
    axis.tick_params(labelsize=8)
fig.suptitle("Run 1: one GPU correctness corpus; one censored frontier cell", fontsize=12)
fig.text(.5,.012,"Original remote ingestion failed; local correction does not pass the pipeline. Frontier: 748.35 s, signal 6 / exit 134, D unmeasured.",ha="center",fontsize=8)
fig.tight_layout(rect=(0,.07,1,.91))
fig.savefig(here/"run1-validation-memory.svg")
fig.savefig(here/"run1-validation-memory.png",dpi=150)
