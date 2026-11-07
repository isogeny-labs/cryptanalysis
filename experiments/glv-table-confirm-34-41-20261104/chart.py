#!/usr/bin/env python3
"""ratios.svg from results.json: cand (cap-128 rule) over main, per-cell 95% intervals, secondary 98.75%, primary 95%."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = json.load(open(HERE / "results.json"))
COL = "#2a6f97"
W, H, x0, x1 = 760, 560, 150, 730
lo_v, hi_v = 0.85, 1.20
xp = lambda v: x0 + (min(max(v, lo_v), hi_v) - lo_v) / (hi_v - lo_v) * (x1 - x0)
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="12">',
     f'<rect width="{W}" height="{H}" fill="white"/>',
     '<text x="10" y="22" font-size="15" font-weight="bold">curve_solve group ops: cap-128 rule over main (cap 32), same targets</text>',
     f'<text x="10" y="42" fill="#444">seed {R["seed"]}; cells 95% bootstrap interval (descriptive); family and size-half rows 98.75% (K = 4); both pooled 95% (K = 1)</text>']
for t in (0.9, 0.95, 1.0, 1.05, 1.1, 1.15):
    o.append(f'<line x1="{xp(t):.1f}" x2="{xp(t):.1f}" y1="60" y2="{H - 60}" stroke="{"#888" if t == 1 else "#e3e3e3"}"/><text x="{xp(t):.1f}" y="{H - 44}" text-anchor="middle">{t:.2f}</text>')
rows = []
for f in ("j1728", "j0"):
    for b in (32, 34, 36, 38, 40):
        c = R["cells"][f"{f}:{b}"]
        rows.append((f"{f} {b}{' (desc.)' if b == 32 else ''}", c["cand_over_main"], *c["ci95"], False))
for k, v in R["secondary"].items():
    rows.append((k.replace("family:", "").replace("sizes:", "bits ") + " pooled", v["geomean_over_main"], *v["ci"], True))
p = R["primary"]
rows.append(("both pooled", p["geomean_over_main"], *p["ci"], True))
for i, (name, pt, lo, hi, bold) in enumerate(rows):
    y = 70 + i * 28
    o.append(f'<text x="{x0 - 8}" y="{y + 10}" text-anchor="end"{" font-weight=\"bold\"" if bold else ""}>{name}</text>')
    o.append(f'<line x1="{xp(lo):.1f}" x2="{xp(hi):.1f}" y1="{y + 6}" y2="{y + 6}" stroke="{COL}" stroke-width="{3 if bold else 2}"/><circle cx="{xp(pt):.1f}" cy="{y + 6}" r="3.5" fill="{COL}"/>')
o.append("</svg>")
(HERE / "ratios.svg").write_text("\n".join(o) + "\n")
