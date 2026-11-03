#!/usr/bin/env python3
"""Coordinate-system leverage bound for the lab's recorded IC rows (derived, not measured).

Reads data.json: per row, the recorded IC/rho gap and the share f_g of the IC
cost that is elliptic-curve group operations (the only part a coordinate
system can change), plus the source path of each number. For a coordinate
factor c (per-group-operation speedup), Amdahl's ceiling on the whole-row
speedup is 1 / ((1 - f_g) + f_g / c). The row reaches parity only if the
ceiling is at least the gap. Writes bound.svg and RESULTS.md.
"""
import json, pathlib, math
HERE = pathlib.Path(__file__).resolve().parent
d = json.loads((HERE / 'data.json').read_text())
rows = d['rows']; cs = d['coordinate_factors']
def ceiling(fg, c): return 1.0 / ((1 - fg) + fg / c) if c != 'inf' else (1.0 / (1 - fg) if fg < 1 else float('inf'))
out = ['# Results', '', 'Ceiling = 1 / ((1 - f_g) + f_g / c): the largest whole-row speedup a per-group-operation factor c can give when only the fraction f_g of the row is group operations. A row reaches parity with rho only if the ceiling is at least the recorded gap.', '',
       '| row | gap IC/rho | f_g (group-op share) | ceiling c=1.3 | ceiling c=2 | ceiling c=3 | ceiling c=inf | parity reachable by coordinates alone? |', '|---|---:|---:|---:|---:|---:|---:|:--|']
for r in rows:
    fg = r['f_g']; gap = r['gap']
    cs_ = [ceiling(fg, c) for c in (1.3, 2, 3, 'inf')]
    reach = 'yes' if cs_[3] >= gap else 'no'
    out.append(f"| {r['label']} | {gap:.3g} | {fg:.3f} | {cs_[0]:.3g} | {cs_[1]:.3g} | {cs_[2]:.3g} | {('inf' if math.isinf(cs_[3]) else f'{cs_[3]:.3g}')} | {reach} |")
out += ['', '## Sources', '']
for r in rows:
    out.append(f"- **{r['label']}**: gap from {r['gap_source']}; f_g from {r['fg_source']}. {r.get('note','')}")
(HERE / 'RESULTS.md').write_text('\n'.join(out) + '\n')
# figure: bars gap vs ceiling(c=2) and ceiling(c=inf), log scale
W, H, left, top, bw = 980, 420, 70, 50, 150
n = len(rows); svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="Helvetica, Arial, sans-serif" font-size="11">', f'<rect width="{W}" height="{H}" fill="white"/>',
    '<text x="70" y="24" font-size="13" font-weight="bold">Recorded gap to matched rho versus the ceiling a coordinate-system change can reach (log scale; derived from frozen rows, no new measurement)</text>']
vals = [r['gap'] for r in rows] + [ceiling(r['f_g'], 2) for r in rows] + [min(ceiling(r['f_g'], 'inf'), 1000) for r in rows]
lo, hi = 0.5, max(vals) * 1.5
def y(v): return top + (H - top - 70) * (1 - (math.log10(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)))
for tick in (0.5, 1, 2, 5, 10, 20, 50, 100):
    if lo <= tick <= hi:
        svg.append(f'<line x1="{left}" y1="{y(tick)}" x2="{W-20}" y2="{y(tick)}" stroke="#ddd"/><text x="{left-6}" y="{y(tick)+4}" text-anchor="end">{tick}</text>')
svg.append(f'<line x1="{left}" y1="{y(1)}" x2="{W-20}" y2="{y(1)}" stroke="#444" stroke-dasharray="4 3"/><text x="{W-22}" y="{y(1)-4}" text-anchor="end" font-size="10">parity with rho</text>')
for i, r in enumerate(rows):
    x0 = left + 20 + i * bw
    for k, (v, col, lab) in enumerate(((r['gap'], '#2b47c9', 'gap'), (ceiling(r['f_g'], 2), '#b9c6ff', 'ceiling c=2'), (min(ceiling(r['f_g'], 'inf'), 1000), '#ffd2a8', 'ceiling c=inf'))):
        x = x0 + k * 34; svg.append(f'<rect x="{x}" y="{y(max(v, lo))}" width="30" height="{y(lo) - y(max(v, lo))}" fill="{col}"/>')
        svg.append(f'<text x="{x+15}" y="{y(max(v, lo))-3}" text-anchor="middle" font-size="9">{v:.3g}</text>')
    svg.append(f'<text x="{x0+50}" y="{H-50}" text-anchor="middle" font-size="10">{r["label"]}</text>')
svg.append(f'<text x="{left}" y="{H-22}" font-size="10">dark: recorded IC/rho gap; light blue: ceiling if every group operation became 2x cheaper; orange: ceiling if group operations became free (c = inf, capped at 1000). Sources in RESULTS.md.</text>')
svg.append('</svg>'); (HERE / 'bound.svg').write_text('\n'.join(svg)); print('wrote RESULTS.md, bound.svg')
