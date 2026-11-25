#!/usr/bin/env python3
"""Stacked bars of summary.json: where ca_rho_solve's operations go."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = json.load(open(HERE / "summary.json"))
parts = [("productive", "productive steps", "#2a6f97"), ("cycle_steps", "steps in fruitless cycles", "#d1495b"),
         ("retry_slots", "look-ahead retries", "#edae49"), ("escape_ops", "cycle-escape scans", "#7b2d26"),
         ("table", "multiplier table", "#8d99ae"), ("starts", "walk starts", "#5c677d"),
         ("restarts", "restarts", "#b8c0d0"), ("other", "abandoned, final round", "#999")]
def share(s, k):
    sh = s["share"]
    if k == "restarts":
        return sh["restart_selfmerge"] + sh["restart_useless"] + sh["restart_abandon"]
    if k == "other":
        return sh["abandon_steps"] + sh["unprocessed"]
    return sh[k]
rows = list(S)
W, bar, gap, left, top = 900, 24, 10, 120, 62
H = top + len(rows) * (bar + gap) + 90
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="12">',
     f'<rect width="{W}" height="{H}" fill="white"/>',
     '<text x="10" y="22" font-size="15" font-weight="bold">Where ca_rho_solve spends its group operations (generic curves, traced)</text>',
     '<text x="10" y="42" fill="#444">share of operations per size; right column: mean S = group_ops / sqrt(order); table size r and walks W in brackets</text>']
span = W - left - 190
for i, k in enumerate(rows):
    y = top + i * (bar + gap)
    s = S[k]
    o.append(f'<text x="{left - 8}" y="{y + 16}" text-anchor="end">{k} bits</text>')
    x = left
    for key, _, col in parts:
        v = share(s, key)
        w = v * span
        o.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{bar}" fill="{col}"/>')
        if w > 30:
            o.append(f'<text x="{x + w / 2:.1f}" y="{y + 16}" text-anchor="middle" fill="white">{v:.0%}</text>')
        x += w
    o.append(f'<text x="{left + span + 8}" y="{y + 16}">S {s["mean_S"]:.2f} (r {s["table_r"][0]}-{s["table_r"][-1]}, W {s["W"][0]}-{s["W"][-1]})</text>')
ly = top + len(rows) * (bar + gap) + 20
for j, (_, name, col) in enumerate(parts):
    lx = 10 + (j % 4) * 215
    yy = ly + (j // 4) * 20
    o.append(f'<rect x="{lx}" y="{yy}" width="12" height="12" fill="{col}"/><text x="{lx + 17}" y="{yy + 11}">{name}</text>')
o.append("</svg>")
(HERE / "breakdown.svg").write_text("\n".join(o))
print("wrote breakdown.svg")
