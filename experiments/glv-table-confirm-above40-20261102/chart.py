#!/usr/bin/env python3
"""ratios.svg from results.json: per-cell 95% intervals and the pooled primary intervals, r64 and r128 vs main."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = json.load(open(HERE / "results.json"))
ARMS = [("r64", "#6a4c93", "table 64"), ("r128", "#2a6f97", "table 128")]
labels = [(f, b) for f in ("j1728", "j0") for b in (42, 44, 46)]
W, H, x0, x1 = 760, 440, 120, 730
lo_v, hi_v = 0.85, 1.15
xp = lambda v: x0 + (min(max(v, lo_v), hi_v) - lo_v) / (hi_v - lo_v) * (x1 - x0)
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="12">',
     f'<rect width="{W}" height="{H}" fill="white"/>',
     '<text x="10" y="22" font-size="15" font-weight="bold">curve_solve group ops relative to main (r = 32), same targets</text>',
     f'<text x="10" y="42" fill="#444">seed {R["seed"]}; cells: 95% bootstrap interval; pooled rows: 97.5% interval (K = 2), family rows 99.17% (K = 6)</text>']
for t in (0.9, 0.95, 1.0, 1.05, 1.1):
    o.append(f'<line x1="{xp(t):.1f}" x2="{xp(t):.1f}" y1="60" y2="{H - 60}" stroke="{"#888" if t == 1 else "#e3e3e3"}"/><text x="{xp(t):.1f}" y="{H - 44}" text-anchor="middle">{t:.2f}</text>')
rows = []
for f, b in labels:
    rows.append((f"{f} {b}", {a: (R["cells"][f"{f}:{b}"]["arms"][a]["over_main"], *R["cells"][f"{f}:{b}"]["arms"][a]["ci95"]) for a, _, _ in ARMS}))
for f in ("j1728", "j0"):
    rows.append((f"{f} pooled", {a: (R["family"][f"{a}:{f}"]["geomean_over_main"], *R["family"][f"{a}:{f}"]["ci"]) for a, _, _ in ARMS}))
rows.append(("both pooled", {a: (R["primary"][a]["geomean_over_main"], *R["primary"][a]["ci"]) for a, _, _ in ARMS}))
for i, (name, d) in enumerate(rows):
    y = 72 + i * 32
    bold = "pooled" in name
    o.append(f'<text x="{x0 - 8}" y="{y + 10}" text-anchor="end"{" font-weight=\"bold\"" if bold else ""}>{name}</text>')
    for j, (a, col, _) in enumerate(ARMS):
        p, lo, hi = d[a]
        yy = y + j * 10
        o.append(f'<line x1="{xp(lo):.1f}" x2="{xp(hi):.1f}" y1="{yy + 4}" y2="{yy + 4}" stroke="{col}" stroke-width="{3 if bold else 2}"/><circle cx="{xp(p):.1f}" cy="{yy + 4}" r="3.5" fill="{col}"/>')
x = 10
for _, col, name in ARMS:
    o.append(f'<line x1="{x}" x2="{x + 24}" y1="{H - 14}" y2="{H - 14}" stroke="{col}" stroke-width="2"/><text x="{x + 30}" y="{H - 10}">{name}</text>')
    x += 110
o.append("</svg>")
(HERE / "ratios.svg").write_text("\n".join(o) + "\n")
