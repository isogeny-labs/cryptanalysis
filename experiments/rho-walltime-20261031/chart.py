#!/usr/bin/env python3
"""walltime.svg: Tier 1 wall-time ratio ref/other per size (above 1 = other faster), run 41220345406."""
import json
from pathlib import Path
H = Path(__file__).resolve().parent / "tier1-github-41220345406"
rows = {}
for s in (28, 32, 36, 40):
    for v, k in (("", "cand"), ("_var", "var")):
        d = json.load(open(H / f"run-summary_{s}{v}.json"))["summary"]
        rows[(s, k)] = (d["observed_ratio_median"], d["bootstrap95_by_pair"])
W, Ht, x0, top, base = 760, 380, 70, 80, 300
lo, hi = 0.80, 1.45
y = lambda v: base - (v - lo) / (hi - lo) * (base - top)
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Ht}" font-family="sans-serif" font-size="12">',
     f'<rect width="{W}" height="{Ht}" fill="white"/>',
     '<text x="10" y="22" font-size="15" font-weight="bold">Plain rho (#1327), Tier 1 wall time: main / other arm</text>',
     '<text x="10" y="42" fill="#444">Above 1 = the other arm is faster. 15 alternating pairs per size, 100 targets per pair, GitHub Actions run 41220345406.</text>',
     '<text x="10" y="58" fill="#444">cand = #1327 head; var = cand with 32 DPs per walk instead of 128 (measurement arm). Bars: median; whiskers: 95% paired bootstrap.</text>']
for t in (0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4):
    o.append(f'<line x1="{x0}" x2="{W-20}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="{"#888" if t == 1.0 else "#e3e3e3"}"/>'
             f'<text x="{x0-6}" y="{y(t)+4:.1f}" text-anchor="end">{t:.1f}</text>')
cols = {"cand": "#2a6f97", "var": "#d1495b"}
for i, s in enumerate((28, 32, 36, 40)):
    cx = x0 + 90 + i * 160
    for j, k in enumerate(("cand", "var")):
        m, ci = rows[(s, k)]
        bx = cx - 52 + j * 54
        o.append(f'<rect x="{bx}" y="{min(y(m), y(1.0)):.1f}" width="46" height="{abs(y(m)-y(1.0)):.1f}" fill="{cols[k]}" fill-opacity="0.75"/>')
        o.append(f'<line x1="{bx+23}" x2="{bx+23}" y1="{y(ci[0]):.1f}" y2="{y(ci[1]):.1f}" stroke="#000" stroke-width="1.5"/>')
        o.append(f'<text x="{bx+23}" y="{(y(m)-6 if m >= 1 else y(m)+14):.1f}" text-anchor="middle" font-size="11">{m:.3f}</text>')
    o.append(f'<text x="{cx}" y="{base+22}" text-anchor="middle" font-weight="bold">{s} bits</text>')
o.append(f'<rect x="{x0}" y="{Ht-34}" width="12" height="12" fill="{cols["cand"]}"/><text x="{x0+18}" y="{Ht-24}">cand</text>')
o.append(f'<rect x="{x0+80}" y="{Ht-34}" width="12" height="12" fill="{cols["var"]}"/><text x="{x0+98}" y="{Ht-24}">var (32 DPs/walk)</text>')
o.append("</svg>")
(Path(__file__).resolve().parent / "walltime.svg").write_text("\n".join(o))
print("wrote walltime.svg")
