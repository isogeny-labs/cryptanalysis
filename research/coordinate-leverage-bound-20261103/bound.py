#!/usr/bin/env python3
"""Coordinate-system leverage for the lab's recorded IC rows (derived, not measured).

For each frozen row: gap = recorded IC/rho; f_g = share of IC cost that is
elliptic-curve group operations (measured where a record gives it, else the
envelope f_g = 1, which is the most favourable assumption for coordinates).
A coordinate change multiplies the cost of each group operation by 1/c and
nothing else, so the whole-row speedup is 1/((1 - f_g) + f_g/c) (Amdahl) and
parity needs c* = f_g / (1/gap - (1 - f_g)), or is unreachable when
1/gap <= 1 - f_g. The available c is bounded by the lab's own pricing of the
alternatives to the shipping batched-affine arithmetic (data.json).
"""
import json, pathlib, math
HERE = pathlib.Path(__file__).resolve().parent
d = json.loads((HERE / 'data.json').read_text())
avail = d['coordinate_factor_available']; c_real, c_gen = avail['realistic'], avail['generous']
def speedup(fg, c): return 1.0 / ((1 - fg) + fg / c)
def required(fg, gap):
    denom = 1.0 / gap - (1 - fg)
    return math.inf if denom <= 0 else fg / denom
rows = []
for r in d['rows']:
    fg, gap = r['f_g'], r['gap']
    rows.append({**r, 'c_star': required(fg, gap), 'at_real': speedup(fg, c_real), 'at_gen': speedup(fg, c_gen),
                 'parity_real': speedup(fg, c_real) >= gap, 'parity_gen': speedup(fg, c_gen) >= gap})
out = ['# Results (derived from frozen records; no new measurement)', '',
       f"Available per-group-operation factor from a coordinate change: realistic c = {c_real} (batch depth is the only lever left once arithmetic is batched affine), generous c = {c_gen} (the ALU ratio read in the lab's favour). Sources in data.json.", '',
       '| row | gap IC/rho | f_g | f_g measured? | c* needed for parity | row speedup at c=1.05 | at c=1.30 | parity at c=1.05? | at c=1.30? |', '|---|---:|---:|:--|---:|---:|---:|:--|:--|']
for r in rows:
    cs = 'unreachable' if math.isinf(r['c_star']) else f"{r['c_star']:.3g}"
    out.append(f"| {r['label']} | {r['gap']:.4g} | {r['f_g']:.3f} | {'yes' if r['f_g_measured'] else 'no (envelope 1)'} | {cs} | {r['at_real']:.3f} | {r['at_gen']:.3f} | {'yes' if r['parity_real'] else 'no'} | {'yes' if r['parity_gen'] else 'no'} |")
out += ['', 'Reading: with f_g = 1 the required factor equals the gap itself, so the smallest gap on record, 1.314 on the n41 cold panel, needs c = 1.314, above the generous 1.30 by 1%; every other row needs c >= 1.566. On the one row with a measured f_g (0.587) parity needs c = ' + f"{rows[0]['c_star']:.2f}" + ', while the available factor is at most 1.05 to 1.30.', '', '## Sources', '']
for r in d['rows']:
    out.append(f"- **{r['label']}**: gap from {r['gap_source']}; f_g: {r['fg_source']} {r.get('note','')}".rstrip())
out += ['', '## Measured coordinate or curve-shape arms in the lab', '', '| arm | numbers | source |', '|---|---|---|']
for a in d['measured_coordinate_arms']:
    out.append(f"| {a['arm']} | {a['numbers']} | {a['source']} |")
(HERE / 'RESULTS.md').write_text('\n'.join(out) + '\n')
# figure: required c* per row versus available c (log scale)
W, H, left, top = 1000, 440, 70, 50
n = len(rows); bw = (W - left - 30) / n
vals = [min(r['c_star'], 100) for r in rows]
lo, hi = 1.0, max(vals) * 1.6
def y(v): return top + (H - top - 90) * (1 - (math.log10(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)))
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="Helvetica, Arial, sans-serif" font-size="11">', f'<rect width="{W}" height="{H}" fill="white"/>',
       '<text x="70" y="24" font-size="13" font-weight="bold">Per-group-operation factor c* a coordinate change would need for parity with rho, per recorded IC row (log scale)</text>']
for tick in (1, 1.3, 2, 3, 5, 10, 20, 50):
    if lo <= tick <= hi:
        svg.append(f'<line x1="{left}" y1="{y(tick)}" x2="{W-20}" y2="{y(tick)}" stroke="#e4e4e4"/><text x="{left-6}" y="{y(tick)+4}" text-anchor="end">{tick}</text>')
for cval, col, lab in ((c_real, '#2a9d4b', f'available, realistic c = {c_real}'), (c_gen, '#d08a00', f'available, generous c = {c_gen}')):
    svg.append(f'<line x1="{left}" y1="{y(cval)}" x2="{W-20}" y2="{y(cval)}" stroke="{col}" stroke-width="2" stroke-dasharray="6 4"/><text x="{W-24}" y="{y(cval)-4}" text-anchor="end" fill="{col}" font-size="10">{lab}</text>')
for i, r in enumerate(rows):
    x = left + i * bw + 12; v = min(r['c_star'], 100)
    col = '#2b47c9' if r['f_g_measured'] else '#9fb0e8'
    svg.append(f'<rect x="{x}" y="{y(v)}" width="{bw-24}" height="{y(lo)-y(v)}" fill="{col}"/>')
    svg.append(f'<text x="{x+(bw-24)/2}" y="{y(v)-4}" text-anchor="middle" font-size="10">{("inf" if math.isinf(r["c_star"]) else f"{r["c_star"]:.3g}")}</text>')
    words = r['label'].split(' '); lines = [' '.join(words[:3]), ' '.join(words[3:6]), ' '.join(words[6:])]
    for k, ln in enumerate(lines):
        if ln: svg.append(f'<text x="{x+(bw-24)/2}" y="{H-66+12*k}" text-anchor="middle" font-size="9">{ln}</text>')
svg.append(f'<text x="{left}" y="{H-14}" font-size="10">dark bar: f_g measured (0.587, Frobenius-orbit n29); light bars: envelope f_g = 1, so c* equals the recorded gap. Every bar sits above both available-c lines. Derived from frozen records (RESULTS.md); nothing here is a new measurement.</text>')
svg.append('</svg>'); (HERE / 'bound.svg').write_text('\n'.join(svg)); print('wrote RESULTS.md, bound.svg')
for r in rows: print(f"{r['label'][:44]:44s} gap {r['gap']:6.3f} f_g {r['f_g']:.3f} c* {r['c_star']:.3g} at1.05 {r['at_real']:.3f} at1.3 {r['at_gen']:.3f}")
