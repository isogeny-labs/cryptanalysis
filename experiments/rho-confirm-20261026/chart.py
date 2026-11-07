#!/usr/bin/env python3
"""confirm.svg: held-out ratio candidate / main per size with Bonferroni intervals, next to the selection round's ratio."""
import json
from pathlib import Path
H = Path(__file__).resolve().parent
R = json.load(open(H / "results.json"))
SEL = {20: 0.666, 24: 0.624, 28: 0.599, 32: 0.886, 36: 0.905, 40: 0.934}  # #1093 results.md, arm F+B+D128+R1.5
sizes = sorted(int(b) for b in R["cells"])
W, left, top, rowh = 760, 90, 70, 34
lo, hi = 0.5, 1.02
X = lambda v: left + (v - lo) / (hi - lo) * (W - left - 30)
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{top + len(sizes) * rowh + 80}" font-family="sans-serif" font-size="12">',
     f'<rect width="{W}" height="{top + len(sizes) * rowh + 80}" fill="white"/>',
     '<text x="10" y="22" font-size="15" font-weight="bold">Held-out confirmation: group_ops, candidate / main (lower is better)</text>',
     f'<text x="10" y="42" fill="#444">filled: held-out ratio with Bonferroni interval; hollow: selection round (#1093); pooled {R["pooled"]:.4f} [{R["pooled_lo"]:.4f}, {R["pooled_hi"]:.4f}]</text>']
o.append(f'<line x1="{X(1):.1f}" y1="{top - 8}" x2="{X(1):.1f}" y2="{top + len(sizes) * rowh}" stroke="#888" stroke-dasharray="3,3"/>')
for i, b in enumerate(sizes):
    c = R["cells"][str(b)]; y = top + i * rowh + 12
    o.append(f'<text x="{left - 10}" y="{y + 4}" text-anchor="end">{b} bits</text>')
    o.append(f'<line x1="{X(c["lo"]):.1f}" y1="{y}" x2="{X(c["hi"]):.1f}" y2="{y}" stroke="#2a6f97" stroke-width="3"/>')
    o.append(f'<circle cx="{X(c["ratio"]):.1f}" cy="{y}" r="4.5" fill="#2a6f97"/>')
    o.append(f'<circle cx="{X(SEL[b]):.1f}" cy="{y + 12}" r="4" fill="white" stroke="#d1495b" stroke-width="2"/>')
    o.append(f'<text x="{X(c["ratio"]) + 8:.1f}" y="{y - 5}" fill="#2a6f97">{c["ratio"]:.3f}</text>')
for t in (0.6, 0.8, 1.0):
    o.append(f'<text x="{X(t):.1f}" y="{top + len(sizes) * rowh + 18}" text-anchor="middle" fill="#666">{t}</text>')
o.append("</svg>")
(H / "confirm.svg").write_text("\n".join(o)); print("wrote confirm.svg")
