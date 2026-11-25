#!/usr/bin/env python3
"""summary.md: what an escape costs on main (from rows_main.jsonl.gz, same solves as the paired run)
and the per-cell paired ratios of results.json."""
import collections, gzip, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
PH = ["setup", "batch", "post", "escape", "restart"]
cells = collections.defaultdict(collections.Counter)
for l in gzip.open(HERE / "rows_main.jsonl.gz", "rt"):
    r = json.loads(l)
    c = cells[(r["family"], r["bits"])]
    c["n"] += 1; c["ops"] += r["ops"]
    for k, v in r.items():
        if isinstance(v, int) and not isinstance(v, bool):
            c[k] += v
def cost(c, ph, d): return c[ph + "_mul"] + 0.8 * c[ph + "_sqr"] + d * c[ph + "_euclid"]
R = json.load(open(HERE / "results.json"))["cells"]
o = ["# Summary", "", "## What an escape costs on main (field multiplications M; S = 0.8 M; division step d M)", "",
     "| cell | W | escapes /1e4 steps | inv per escape | division steps per inv | step M (d=1/2.5/5) | escape M (d=1/2.5/5) | escape / step (d=2.5) | escape share of walk cost (d=1/2.5/5) |",
     "|---|---|---|---|---|---|---|---|---|"]
for key in sorted(cells):
    c = cells[key]; st = c["batch_walks"]; esc = c["esc2"] + c["esc4"]
    step = [(cost(c, "batch", d) + cost(c, "post", d)) / st for d in (1, 2.5, 5)]
    e = [cost(c, "escape", d) / esc for d in (1, 2.5, 5)]
    tot = [sum(cost(c, p, d) for p in PH) for d in (1, 2.5, 5)]
    sh = [100 * cost(c, "escape", d) / t for d, t in zip((1, 2.5, 5), tot)]
    o.append(f"| {key[0]} {key[1]} | {st / c['batches']:.1f} | {1e4 * esc / st:.2f} | {c['escape_inv'] / esc:.2f} | {c['escape_euclid'] / c['escape_inv']:.1f} | "
             + "/".join(f"{x:.1f}" for x in step) + " | " + "/".join(f"{x:.1f}" for x in e) + f" | {e[1] / step[1]:.1f} | " + "/".join(f"{x:.3f}%" for x in sh) + " |")
o += ["", "## Paired field-cost ratios, batch escape / main (Bonferroni 36 intervals)", "",
      "| cell | d=1 | d=2.5 | d=5 | group ops | inversions | escapes (main / batch) |", "|---|---|---|---|---|---|---|"]
for k, c in sorted(R.items()):
    f = lambda n: f"{c[n]['ratio']:.5f} [{c[n]['lo']:.5f}, {c[n]['hi']:.5f}]"
    o.append(f"| {k} | {f('cost1.0')} | {f('cost2.5')} | {f('cost5.0')} | {f('ops')} | {f('inv')} | {c['escapes_main']} / {c['escapes_candidate']} |")
(HERE / "summary.md").write_text("\n".join(o) + "\n")
print("\n".join(o))
