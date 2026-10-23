#!/usr/bin/env python3
"""fade.svg from breakdown.json and paired.json: (A) how often the GLV walk enters a
fruitless cycle, by size and multiplier-table size; (B) paired curve_solve ratios."""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
BD = json.load(open(HERE / "breakdown.json"))
PR = json.load(open(HERE / "paired.json"))
SIZES = [24, 28, 32, 36, 40]
W, H = 980, 470
PW, top, base = 430, 80, 360
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="12">',
     f'<rect width="{W}" height="{H}" fill="white"/>',
     '<text x="10" y="22" font-size="15" font-weight="bold">Why the cycle escape fades with size: the multiplier table grows from 8 to 32</text>',
     '<text x="10" y="42" fill="#444">30 curves x 40 targets per family and size, same curves and targets in every build; main 3ce4c29 + v2-curve.patch walks, traced</text>']
COL = {"j1728": "#2a6f97", "j0": "#d1495b"}


def xpos(x0, bits):
    return x0 + 30 + (bits - 24) / 16 * (PW - 70)


# Panel A: cycle entries per 1e4 committed steps, log scale 0.1 .. 30
xa = 60
ylog = lambda v: base - (math.log10(max(v, 0.1)) + 1) / (math.log10(30) + 1) * (base - top)
for t in (0.1, 0.3, 1, 3, 10, 30):
    y = ylog(t)
    o.append(f'<line x1="{xa}" x2="{xa + PW - 30}" y1="{y:.1f}" y2="{y:.1f}" stroke="#e3e3e3"/><text x="{xa - 6}" y="{y + 4:.1f}" text-anchor="end">{t:g}</text>')
o.append(f'<text x="{xa - 45}" y="{(top + base) / 2}" transform="rotate(-90 {xa - 45} {(top + base) / 2})" text-anchor="middle">cycle entries per 10^4 steps</text>')
for b in SIZES:
    r = BD[f"legacy:j1728:{b}"]["mult_r"]
    o.append(f'<text x="{xpos(xa, b):.1f}" y="{base + 16}" text-anchor="middle">{b}</text>'
             f'<text x="{xpos(xa, b):.1f}" y="{base + 30}" text-anchor="middle" fill="#666" font-size="10">r={"/".join(map(str, r))}</text>')
o.append(f'<text x="{xa + (PW - 30) / 2}" y="{base + 48}" text-anchor="middle">subgroup bits (r = multiplier-table size chosen by main)</text>')
for fam in ("j1728", "j0"):
    for build, dash in (("legacy", ""), ("r32legacy", "5,4")):
        pts = [(xpos(xa, b), ylog(BD[f"{build}:{fam}:{b}"]["cycle_entries_per_1e4_steps"])) for b in SIZES if f"{build}:{fam}:{b}" in BD]
        o.append(f'<polyline fill="none" stroke="{COL[fam]}" stroke-width="2" stroke-dasharray="{dash}" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}"/>')
        for x, y in pts:
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{COL[fam]}"/>')
o.append(f'<text x="{xa}" y="{top - 12}" font-weight="bold">A. Main\'s walk without escape: fruitless-cycle entries</text>')

# Panel B: paired ratios with 95% intervals, linear 0.5 .. 1.5
xb = 560
ylin = lambda v: base - (v - 0.5) / 1.0 * (base - top)
for t in (0.5, 0.75, 1.0, 1.25, 1.5):
    y = ylin(t)
    o.append(f'<line x1="{xb}" x2="{xb + PW - 30}" y1="{y:.1f}" y2="{y:.1f}" stroke="{"#999" if t == 1 else "#e3e3e3"}"/><text x="{xb - 6}" y="{y + 4:.1f}" text-anchor="end">{t:.2f}</text>')
for b in SIZES:
    o.append(f'<text x="{xpos(xb, b):.1f}" y="{base + 16}" text-anchor="middle">{b}</text>')
o.append(f'<text x="{xb + (PW - 30) / 2}" y="{base + 48}" text-anchor="middle">subgroup bits</text>')
for fam, dx in (("j1728", -4), ("j0", 4)):
    for pair, dash in (("escape/legacy", ""), ("r32escape/escape", "5,4")):
        pts = []
        for b in SIZES:
            e = PR.get(f"{pair}:{fam}:{b}")
            if not e:
                continue
            x = xpos(xb, b) + dx
            lo, hi = e["ci95"]
            o.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{ylin(lo):.1f}" y2="{ylin(hi):.1f}" stroke="{COL[fam]}"/>')
            pts.append((x, ylin(e["ratio"])))
        o.append(f'<polyline fill="none" stroke="{COL[fam]}" stroke-width="2" stroke-dasharray="{dash}" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}"/>')
        for x, y in pts:
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{COL[fam]}"/>')
o.append(f'<text x="{xb}" y="{top - 12}" font-weight="bold">B. Paired curve_solve operations, ratio (95% CI)</text>')

# legend
ly = H - 22
items = [("#2a6f97", "", "j = 1728"), ("#d1495b", "", "j = 0"),
         ("#555", "", "A: table chosen by main · B: escape / no escape"),
         ("#555", "5,4", "A: table forced to 32 · B: table 32 / main (both with escape)")]
x = 10
for col, dash, name in items:
    o.append(f'<line x1="{x}" x2="{x + 26}" y1="{ly}" y2="{ly}" stroke="{col}" stroke-width="2" stroke-dasharray="{dash}"/><text x="{x + 32}" y="{ly + 4}">{name}</text>')
    x += 40 + 7 * len(name)
o.append("</svg>")
(HERE / "fade.svg").write_text("\n".join(o))
print("wrote fade.svg")
