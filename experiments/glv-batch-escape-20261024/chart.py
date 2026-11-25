#!/usr/bin/env python3
"""ratios.svg from results.json: field cost of the batch-escape arm over main, per size, at the
three inversion prices, Bonferroni-adjusted intervals; one panel per family."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = json.load(open(HERE / "results.json"))
C = R["cells"]
SIZES = sorted({int(k.split(":")[1]) for k in C})
PR = [("cost1.0", "#edae49", "1"), ("cost2.5", "#2a6f97", "2.5"), ("cost5.0", "#d1495b", "5")]
W, H, PW, top, base = 1010, 450, 450, 90, 350
lo_v, hi_v = 0.994, 1.002
y = lambda v: base - (min(max(v, lo_v), hi_v) - lo_v) / (hi_v - lo_v) * (base - top)
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="12">',
     f'<rect width="{W}" height="{H}" fill="white"/>',
     '<text x="10" y="22" font-size="15" font-weight="bold">Field-operation cost with the escape inside the batch, relative to main (below 1 = cheaper)</text>',
     f'<text x="10" y="42" fill="#444">{R["n_solves"]} paired solves per arm, seed 20261025; bars: Bonferroni-adjusted bootstrap intervals over curves (36 intervals); colours: price of one inversion division step</text>']
for pi, (fam, title) in enumerate((("j1728", "j = 1728"), ("j0", "j = 0"))):
    x0 = 60 + pi * (PW + 40)
    xp = lambda b: x0 + 20 + (b - SIZES[0]) / (SIZES[-1] - SIZES[0]) * (PW - 60)
    for t in (0.994, 0.996, 0.998, 1.0, 1.002):
        o.append(f'<line x1="{x0}" x2="{x0 + PW - 20}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="{"#888" if t == 1 else "#e3e3e3"}"/><text x="{x0 - 6}" y="{y(t) + 4:.1f}" text-anchor="end">{t:.3f}</text>')
    for b in SIZES:
        o.append(f'<text x="{xp(b):.1f}" y="{base + 16}" text-anchor="middle">{b}</text>')
    o.append(f'<text x="{x0 + (PW - 20) / 2}" y="{base + 36}" text-anchor="middle">subgroup bits</text>')
    o.append(f'<text x="{x0}" y="{top - 12}" font-weight="bold">{title}</text>')
    for ai, (k, col, _) in enumerate(PR):
        for b in SIZES:
            c = C[f"{fam}:{b}"][k]
            x = xp(b) + (ai - 1) * 9
            o.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y(c["lo"]):.1f}" y2="{y(c["hi"]):.1f}" stroke="{col}" stroke-width="2"/>'
                     f'<circle cx="{x:.1f}" cy="{y(c["ratio"]):.1f}" r="3" fill="{col}"/>')
for i, (_, col, lab) in enumerate(PR):
    o.append(f'<circle cx="{70 + i * 190}" cy="{H - 14}" r="4" fill="{col}"/><text x="{80 + i * 190}" y="{H - 10}">division step = {lab}</text>')
o.append('</svg>')
(HERE / "ratios.svg").write_text("\n".join(o))
