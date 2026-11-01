#!/usr/bin/env python3
"""walltime.svg: Tier 1 wall-time ratio main / size-dependent cap per cell, beside the panel's operation ratio."""
import json
from pathlib import Path
H = Path(__file__).resolve().parent
res = json.load(open(H / "results.json"))
sizes = [38, 40, 41, 42, 44, 46, 48]
W, Ht, x0, base, top = 780, 560, 70, 0, 0
lo, hi = 0.70, 1.30
rows = [("j1728", "j = 1728", "#2a6f97", 70, 250), ("j0", "j = 0", "#d1495b", 330, 510)]
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Ht}" font-family="sans-serif" font-size="12">',
     f'<rect width="{W}" height="{Ht}" fill="white"/>',
     '<text x="10" y="20" font-size="15" font-weight="bold">Size-dependent GLV table cap (#1341), Tier 1 wall time: main / candidate</text>',
     '<text x="10" y="38" fill="#444">Above 1 = candidate faster. 15 alternating pairs per cell, GitHub Actions run 41259818507. 38 bits = null cell (identical code).</text>',
     '<text x="10" y="54" fill="#444">Bar: median wall ratio, 95% paired bootstrap whisker. Black tick: the panel\'s operation ratio (fixed by the seeded walks).</text>']
for fam, label, col, top, base in rows:
    y = lambda v, top=top, base=base: base - (v - lo) / (hi - lo) * (base - top)
    o.append(f'<text x="10" y="{top-8}" font-weight="bold" fill="{col}">{label}</text>')
    for t in (0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3):
        o.append(f'<line x1="{x0}" x2="{W-20}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="{"#888" if t == 1.0 else "#e3e3e3"}"/>'
                 f'<text x="{x0-6}" y="{y(t)+4:.1f}" text-anchor="end">{t:.1f}</text>')
    for i, b in enumerate(sizes):
        r = res[f"{fam}_{b}"]
        cx = x0 + 45 + i * 98
        m, ci, op = r["wall_ratio_ref_over_cand"], r["wall_ci95"], r["ops_ratio_ref_over_cand"]
        o.append(f'<rect x="{cx-26}" y="{min(y(m), y(1.0)):.1f}" width="52" height="{abs(y(m)-y(1.0)):.1f}" fill="{col}" fill-opacity="{0.3 if b == 38 else 0.75}"/>')
        o.append(f'<line x1="{cx}" x2="{cx}" y1="{y(ci[0]):.1f}" y2="{y(ci[1]):.1f}" stroke="#000" stroke-width="1.5"/>')
        o.append(f'<line x1="{cx-32}" x2="{cx+32}" y1="{y(op):.1f}" y2="{y(op):.1f}" stroke="#000" stroke-width="2.5"/>')
        ty = y(max(m, op)) - 6 if m >= 1 else y(min(m, op)) + 14
        o.append(f'<text x="{cx}" y="{ty:.1f}" text-anchor="middle" font-size="11">{m:.3f}</text>')
        o.append(f'<text x="{cx}" y="{base+18}" text-anchor="middle" font-weight="bold">{b}b{" null" if b == 38 else ""}</text>')
o.append("</svg>")
(H / "walltime.svg").write_text("\n".join(o))
print("wrote walltime.svg")
