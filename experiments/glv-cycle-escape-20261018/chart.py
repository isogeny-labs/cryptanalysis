#!/usr/bin/env python3
"""Grouped bars from results_v2.json: curve_solve / rho per arm and family, pooled over sizes."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = json.load(open(HERE / "results_v2.json"))
rows = {(x["variant"], x["family"]): x for x in R["vs_rho"] if x["r_bits"] == "all"}
arms = [("legacy", "main's walk", "#8d99ae"), ("patched", "look-ahead fix", "#edae49"), ("escape", "look-ahead fix + cycle escape", "#2a6f97")]
fams = [("j1728", "j = 1728 (|Aut| = 4)"), ("j0", "j = 0 (|Aut| = 6)")]
W, H, left, base, top = 640, 340, 60, 270, 60
scale = 200 / 1.0
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="12">', f'<rect width="{W}" height="{H}" fill="white"/>',
     '<text x="10" y="22" font-size="15" font-weight="bold">curve_solve / negation-map rho, group operations (lower is better)</text>',
     '<text x="10" y="42" fill="#444">paired over 120 curves x 200 targets per family; dashed: theory sqrt(2/|Aut|); bars: 98.75% interval</text>']
for t in (0, 0.25, 0.5, 0.75, 1.0):
    y = base - t * scale
    o.append(f'<line x1="{left}" x2="{W - 20}" y1="{y}" y2="{y}" stroke="#ddd"/><text x="{left - 6}" y="{y + 4}" text-anchor="end">{t:.2f}</text>')
gw, bw = 260, 60
for gi, (fam, label) in enumerate(fams):
    gx = left + 30 + gi * (gw + 30)
    th = rows[("legacy", fam)]["theory"]
    o.append(f'<line x1="{gx - 10}" x2="{gx + gw - 30}" y1="{base - th * scale}" y2="{base - th * scale}" stroke="#d1495b" stroke-dasharray="5,4"/>')
    for ai, (arm, _, col) in enumerate(arms):
        x = gx + ai * (bw + 15)
        r = rows[(arm, fam)]
        h = r["ratio"] * scale
        o.append(f'<rect x="{x}" y="{base - h:.1f}" width="{bw}" height="{h:.1f}" fill="{col}"/>')
        lo, hi = r["ci"]
        o.append(f'<line x1="{x + bw / 2}" x2="{x + bw / 2}" y1="{base - lo * scale:.1f}" y2="{base - hi * scale:.1f}" stroke="black"/>')
        o.append(f'<text x="{x + bw / 2}" y="{base - h - 6:.1f}" text-anchor="middle">{r["ratio"]:.3f}</text>')
    o.append(f'<text x="{gx + (3 * bw + 30) / 2}" y="{base + 18}" text-anchor="middle">{label}</text>')
for ai, (_, name, col) in enumerate(arms):
    lx = 10 + ai * 205
    o.append(f'<rect x="{lx}" y="{H - 22}" width="12" height="12" fill="{col}"/><text x="{lx + 17}" y="{H - 12}">{name}</text>')
o.append("</svg>")
(HERE / "ratios.svg").write_text("\n".join(o))
print("wrote ratios.svg")
