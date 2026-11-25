#!/usr/bin/env python3
"""Stacked bars of summary.json: where glv_rho_solve's operations go."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = json.load(open(HERE / "summary.json"))
parts = [("share_productive", "productive steps", "#2a6f97"), ("share_cycle_steps", "steps in fruitless cycles", "#d1495b"),
         ("share_retries", "look-ahead retries", "#edae49"), ("share_table_starts_restarts", "table, starts, restarts", "#8d99ae")]
rows = [k for k in S]
W, bar, gap, left, top = 760, 22, 10, 170, 60
H = top + len(rows) * (bar + gap) + 70
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="12">',
     f'<rect width="{W}" height="{H}" fill="white"/>',
     '<text x="10" y="22" font-size="15" font-weight="bold">Where glv_rho_solve spends its group operations (upstream main, traced)</text>',
     '<text x="10" y="42" fill="#444">share of operations per solve family; right column: curve_solve / rho ratio (theory in brackets)</text>']
span = W - left - 130
for i, k in enumerate(rows):
    y = top + i * (bar + gap)
    s = S[k]
    o.append(f'<text x="{left - 8}" y="{y + 15}" text-anchor="end">{k.replace(" r=", ", r = ")} bits</text>')
    x = left
    for key, _, col in parts:
        w = s[key] * span
        o.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{bar}" fill="{col}"/>')
        if w > 34:
            o.append(f'<text x="{x + w / 2:.1f}" y="{y + 15}" text-anchor="middle" fill="white">{s[key]:.0%}</text>')
        x += w
    o.append(f'<text x="{left + span + 8}" y="{y + 15}">{s["ratio_curve_solve_vs_rho"]:.3f} ({s["theory_ratio"]:.3f})</text>')
ly = top + len(rows) * (bar + gap) + 20
for j, (_, name, col) in enumerate(parts):
    lx = 10 + j * 185
    o.append(f'<rect x="{lx}" y="{ly}" width="12" height="12" fill="{col}"/><text x="{lx + 17}" y="{ly + 11}">{name}</text>')
o.append("</svg>")
(HERE / "breakdown.svg").write_text("\n".join(o))
print("wrote breakdown.svg")
