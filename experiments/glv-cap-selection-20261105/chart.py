#!/usr/bin/env python3
"""ratios.svg from results.json: per-size pooled and per-cell 95% intervals, r64 and r128 vs main, with the fitted trend."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = json.load(open(HERE / "results.json"))
ARMS = [("r64", "#6a4c93", "table 64"), ("r128", "#2a6f97", "table 128")]
SIZES = (38, 39, 40, 41, 42)
W, H, x0, x1 = 760, 560, 130, 730
lo_v, hi_v = 0.88, 1.12
xp = lambda v: x0 + (min(max(v, lo_v), hi_v) - lo_v) / (hi_v - lo_v) * (x1 - x0)
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="12">',
     f'<rect width="{W}" height="{H}" fill="white"/>',
     '<text x="10" y="22" font-size="15" font-weight="bold">curve_solve group ops relative to main (r = 32), same targets</text>',
     f'<text x="10" y="42" fill="#444">seed {R["seed"]}; 700 curves per cell; 95% bootstrap intervals; pooled = both families (geometric mean)</text>']
for t in (0.9, 0.95, 1.0, 1.05, 1.1):
    o.append(f'<line x1="{xp(t):.1f}" x2="{xp(t):.1f}" y1="60" y2="{H - 60}" stroke="{"#888" if t == 1 else "#e3e3e3"}"/><text x="{xp(t):.1f}" y="{H - 44}" text-anchor="middle">{t:.2f}</text>')
rows = []
for b in SIZES:
    rows.append((f"{b} bits pooled", {a: (R["sizes"][f"{a}:{b}"]["over_main"], *R["sizes"][f"{a}:{b}"]["ci95"]) for a, _, _ in ARMS}, True))
    for f in ("j1728", "j0"):
        c = R["cells"][f"{f}:{b}"]
        rows.append((f"  {f} {b}", {a: (c[a]["over_main"], *c[a]["ci95"]) for a, _, _ in ARMS}, False))
for i, (name, d, bold) in enumerate(rows):
    y = 64 + i * 28
    o.append(f'<text x="{x0 - 8}" y="{y + 10}" text-anchor="end" xml:space="preserve"{" font-weight=\"bold\"" if bold else ""}>{name}</text>')
    for j, (a, col, _) in enumerate(ARMS):
        p, lo, hi = d[a]
        yy = y + j * 9
        o.append(f'<line x1="{xp(lo):.1f}" x2="{xp(hi):.1f}" y1="{yy + 4}" y2="{yy + 4}" stroke="{col}" stroke-width="{3 if bold else 1.5}"/><circle cx="{xp(p):.1f}" cy="{yy + 4}" r="{3.5 if bold else 2.5}" fill="{col}"/>')
x = 10
for _, col, name in ARMS:
    o.append(f'<line x1="{x}" x2="{x + 24}" y1="{H - 14}" y2="{H - 14}" stroke="{col}" stroke-width="2"/><text x="{x + 30}" y="{H - 10}">{name}</text>')
    x += 110
o.append("</svg>")
(HERE / "ratios.svg").write_text("\n".join(o) + "\n")
