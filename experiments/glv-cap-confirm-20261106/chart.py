#!/usr/bin/env python3
"""ratios.svg from results.json: candidate over main per cell (95%), per size (98.75% Bonferroni) and the pooled primary (97.5%)."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = json.load(open(HERE / "results.json"))
W, H, x0, x1 = 760, 460, 130, 730
lo_v, hi_v = 0.90, 1.10
xp = lambda v: x0 + (min(max(v, lo_v), hi_v) - lo_v) / (hi_v - lo_v) * (x1 - x0)
C = "#2a6f97"
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="12">',
     f'<rect width="{W}" height="{H}" fill="white"/>',
     '<text x="10" y="22" font-size="15" font-weight="bold">candidate (cap 128 from 40 bits) group ops relative to main</text>',
     f'<text x="10" y="42" fill="#444">seed {R["seed"]}; {R["n"]} curves per cell; cells 95%, sizes 98.75% (Bonferroni), pooled 97.5%</text>']
for t in (0.9, 0.95, 1.0, 1.05, 1.1):
    o.append(f'<line x1="{xp(t):.1f}" x2="{xp(t):.1f}" y1="60" y2="{H - 60}" stroke="{"#888" if t == 1 else "#e3e3e3"}"/><text x="{xp(t):.1f}" y="{H - 44}" text-anchor="middle">{t:.2f}</text>')
rows = []
for b in (40, 41, 42, 43):
    s = R["by_size"][str(b)]
    rows.append((f"{b} bits pooled", (s["geomean_over_main"], *s["ci_bonferroni"]), True))
    for f in ("j1728", "j0"):
        c = R["cells"][f"{f}:{b}"]
        rows.append((f"  {f} {b}", (c["over_main"], *c["ci95"]), False))
p = R["primary"]
rows.append(("all 8 cells", (p["geomean_over_main"], *p["ci"]), True))
for i, (name, (v, lo, hi), bold) in enumerate(rows):
    y = 70 + i * 24
    o.append(f'<text x="{x0 - 8}" y="{y + 10}" text-anchor="end" xml:space="preserve"{" font-weight=\"bold\"" if bold else ""}>{name}</text>')
    o.append(f'<line x1="{xp(lo):.1f}" x2="{xp(hi):.1f}" y1="{y + 6}" y2="{y + 6}" stroke="{C}" stroke-width="{3 if bold else 1.5}"/><circle cx="{xp(v):.1f}" cy="{y + 6}" r="{4 if bold else 2.5}" fill="{C}"/>')
o.append("</svg>")
(HERE / "ratios.svg").write_text("\n".join(o) + "\n")
