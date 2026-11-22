#!/usr/bin/env python3
"""walltime.svg: Tier 1 wall-time ratio main / cap-128 per cell, beside the panel's operation ratio (results.json)."""
import json
from pathlib import Path
H = Path(__file__).resolve().parent
res = json.load(open(H / "results.json"))
cells = ["j1728_42", "j1728_44", "j1728_46", "j0_42", "j0_44", "j0_46"]
W, Ht, x0, top, base = 760, 380, 70, 80, 300
lo, hi = 0.90, 1.35
y = lambda v: base - (v - lo) / (hi - lo) * (base - top)
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Ht}" font-family="sans-serif" font-size="12">',
     f'<rect width="{W}" height="{Ht}" fill="white"/>',
     '<text x="10" y="22" font-size="15" font-weight="bold">128-entry GLV table, Tier 1 wall time: main (32) / cap 128</text>',
     '<text x="10" y="42" fill="#444">Above 1 = cap 128 is faster. 15 alternating pairs per cell, 20 targets per pair, GitHub Actions run 41234470385.</text>',
     '<text x="10" y="58" fill="#444">Bars: median wall ratio with 95% paired bootstrap whiskers. Black tick: the panel\'s operation ratio (fixed by the walks).</text>']
for t in (0.9, 1.0, 1.1, 1.2, 1.3):
    o.append(f'<line x1="{x0}" x2="{W-20}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="{"#888" if t == 1.0 else "#e3e3e3"}"/>'
             f'<text x="{x0-6}" y="{y(t)+4:.1f}" text-anchor="end">{t:.1f}</text>')
for i, c in enumerate(cells):
    r = res[c]
    cx = x0 + 55 + i * 112
    m, ci, op = r["wall_ratio_ref_over_cand"], r["wall_ci95"], r["ops_ratio_ref_over_cand"]
    col = "#2a6f97" if c.startswith("j1728") else "#d1495b"
    o.append(f'<rect x="{cx-26}" y="{min(y(m), y(1.0)):.1f}" width="52" height="{abs(y(m)-y(1.0)):.1f}" fill="{col}" fill-opacity="0.75"/>')
    o.append(f'<line x1="{cx}" x2="{cx}" y1="{y(ci[0]):.1f}" y2="{y(ci[1]):.1f}" stroke="#000" stroke-width="1.5"/>')
    o.append(f'<line x1="{cx-32}" x2="{cx+32}" y1="{y(op):.1f}" y2="{y(op):.1f}" stroke="#000" stroke-width="2.5"/>')
    o.append(f'<text x="{cx}" y="{(y(max(m, op))-8):.1f}" text-anchor="middle" font-size="11">{m:.3f}</text>' if m >= 1 else
             f'<text x="{cx}" y="{(y(min(m, op))+16):.1f}" text-anchor="middle" font-size="11">{m:.3f}</text>')
    o.append(f'<text x="{cx}" y="{base+22}" text-anchor="middle" font-weight="bold">{c.split("_")[0]} {c.split("_")[1]}b</text>')
o.append(f'<rect x="{x0}" y="{Ht-34}" width="12" height="12" fill="#2a6f97"/><text x="{x0+18}" y="{Ht-24}">j = 1728</text>')
o.append(f'<rect x="{x0+100}" y="{Ht-34}" width="12" height="12" fill="#d1495b"/><text x="{x0+118}" y="{Ht-24}">j = 0</text>')
o.append("</svg>")
(H / "walltime.svg").write_text("\n".join(o))
print("wrote walltime.svg")
