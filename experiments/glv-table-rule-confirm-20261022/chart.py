#!/usr/bin/env python3
"""confirm.svg from results.json: c = 12 over main per size (cell intervals), and each
build's curve_solve / rho, both families."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = json.load(open(HERE / "results.json"))
cells = R["cells"]
SIZES = sorted({int(k.split(":")[1]) for k in cells})
COL = {"j1728": "#2a6f97", "j0": "#d1495b"}
W, H, PW, top, base = 1010, 470, 450, 80, 370
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="12">',
     f'<rect width="{W}" height="{H}" fill="white"/>',
     '<text x="10" y="22" font-size="15" font-weight="bold">Held-out confirmation: GLV table budget constant 48 → 12 (seed 20261023, 200 curves x 25 targets per point)</text>',
     '<text x="10" y="42" fill="#444">' + "; ".join(f"{f}: geomean 28–34 bits {e['geomean_28_34']:.3f} [{e['ci'][0]:.3f}, {e['ci'][1]:.3f}] (97.5%)" for f, e in R["primary"].items()) + '</text>']


def panel(x0, title, lo, hi, series):
    y = lambda v: base - (v - lo) / (hi - lo) * (base - top)
    xp = lambda b: x0 + 20 + (b - SIZES[0]) / (SIZES[-1] - SIZES[0]) * (PW - 60)
    step = (hi - lo) / 4
    for i in range(5):
        t = lo + i * step
        o.append(f'<line x1="{x0}" x2="{x0 + PW - 20}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="{"#888" if abs(t - 1) < 1e-9 else "#e3e3e3"}"/><text x="{x0 - 6}" y="{y(t) + 4:.1f}" text-anchor="end">{t:.2f}</text>')
    for b in SIZES:
        o.append(f'<text x="{xp(b):.1f}" y="{base + 16}" text-anchor="middle">{b}</text>')
    o.append(f'<text x="{x0 + (PW - 20) / 2}" y="{base + 34}" text-anchor="middle">subgroup bits</text>')
    o.append(f'<text x="{x0}" y="{top - 12}" font-weight="bold">{title}</text>')
    for fam, key, dash, ci in series:
        pts = []
        for b in SIZES:
            c = cells[f"{fam}:{b}"]
            x = xp(b) + (-3 if fam == "j1728" else 3)
            if ci:
                l, h = c["ci_cell"]
                o.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y(l):.1f}" y2="{y(h):.1f}" stroke="{COL[fam]}"/>')
            pts.append((x, y(c[key])))
        o.append(f'<polyline fill="none" stroke="{COL[fam]}" stroke-width="2" stroke-dasharray="{dash}" points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}"/>')
        o.extend(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="3" fill="{COL[fam]}"/>' for a, b in pts)


panel(60, "A. c = 12 / main, curve_solve group ops (99.69% intervals)", 0.85, 1.05,
      [("j1728", "c12_over_main", "", True), ("j0", "c12_over_main", "", True)])
panel(550, "B. curve_solve / negation-map rho (solid: c = 12, dashed: main)", 0.40, 0.80,
      [(f, k, d, False) for f in ("j1728", "j0") for k, d in (("c12_over_rho", ""), ("main_over_rho", "5,4"))])
x = 10
for fam, name in (("j1728", "j = 1728"), ("j0", "j = 0")):
    o.append(f'<line x1="{x}" x2="{x + 24}" y1="{H - 22}" y2="{H - 22}" stroke="{COL[fam]}" stroke-width="2"/><text x="{x + 30}" y="{H - 18}">{name}</text>')
    x += 120
o.append("</svg>")
(HERE / "confirm.svg").write_text("\n".join(o))
print("wrote confirm.svg")
