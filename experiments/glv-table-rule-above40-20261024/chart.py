#!/usr/bin/env python3
"""ratios.svg from results.json: each arm's curve_solve ops over main per size, Bonferroni interval, one panel per family."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = json.load(open(HERE / "results.json"))["cells"]
SIZES = sorted({int(k.split(":")[1]) for k in R})
ARMS = [("r64", "#6a4c93", "table 64"), ("r128", "#2a6f97", "table 128"), ("noesc", "#d1495b", "cycle escape off")]
W, H, PW, top, base = 1010, 470, 450, 80, 370
lo_v, hi_v = 0.4, 1.8
y = lambda v: base - (min(max(v, lo_v), hi_v) - lo_v) / (hi_v - lo_v) * (base - top)
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="12">',
     f'<rect width="{W}" height="{H}" fill="white"/>',
     '<text x="10" y="22" font-size="15" font-weight="bold">curve_solve group operations relative to main (r = 32), same targets</text>',
     '<text x="10" y="42" fill="#444">one target per curve, seed 20261031; bars: Bonferroni-adjusted interval (K = 36); values outside 0.4-1.8 are clipped</text>']
for pi, (fam, title) in enumerate((("j1728", "j = 1728"), ("j0", "j = 0"))):
    x0 = 60 + pi * (PW + 40)
    xp = lambda b: x0 + 20 + (b - SIZES[0]) / (SIZES[-1] - SIZES[0]) * (PW - 60)
    for t in (0.5, 0.75, 1.0, 1.25, 1.5, 1.75):
        o.append(f'<line x1="{x0}" x2="{x0 + PW - 20}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="{"#888" if t == 1 else "#e3e3e3"}"/><text x="{x0 - 6}" y="{y(t) + 4:.1f}" text-anchor="end">{t:.2f}</text>')
    for b in SIZES:
        n = R[f"{fam}:{b}"]["targets"]
        o.append(f'<text x="{xp(b):.1f}" y="{base + 16}" text-anchor="middle">{b}</text><text x="{xp(b):.1f}" y="{base + 30}" text-anchor="middle" font-size="10" fill="#666">n={n}</text>')
    o.append(f'<text x="{x0 + (PW - 20) / 2}" y="{base + 48}" text-anchor="middle">subgroup bits</text><text x="{x0}" y="{top - 12}" font-weight="bold">{title}</text>')
    for ai, (arm, col, _) in enumerate(ARMS):
        pts = []
        for b in SIZES:
            e = R[f"{fam}:{b}"]["arms"][arm]
            x = xp(b) + (ai - 1) * 5
            lo, hi = e["ci_adjusted"]
            o.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y(lo):.1f}" y2="{y(hi):.1f}" stroke="{col}" stroke-opacity="0.7"/>')
            pts.append((x, y(e["over_main"])))
        o.append(f'<polyline fill="none" stroke="{col}" stroke-width="2" points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}"/>')
        o += [f'<circle cx="{a:.1f}" cy="{b:.1f}" r="3" fill="{col}"/>' for a, b in pts]
x = 10
for _, col, name in ARMS:
    o.append(f'<line x1="{x}" x2="{x + 24}" y1="{H - 22}" y2="{H - 22}" stroke="{col}" stroke-width="2"/><text x="{x + 30}" y="{H - 18}">{name}</text>')
    x += 50 + 7 * len(name)
o.append("</svg>")
(HERE / "ratios.svg").write_text("\n".join(o))
print("wrote ratios.svg")
