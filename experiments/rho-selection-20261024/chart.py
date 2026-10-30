#!/usr/bin/env python3
"""Chart of results.json: per-size ratio (arm / base) with Bonferroni intervals, and the pooled ratio."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = json.load(open(HERE / "results.json"))
sizes = R["sizes"]
arms = list(R["arms"])
cols = ["#2a6f97", "#3a8fb7", "#5aa9c8", "#8d99ae", "#d1495b", "#edae49"]
W, rowh, left, top = 980, 22, 170, 70
panels = ["pooled"] + [str(b) for b in sizes]
pw = (W - left - 20) / len(panels)
lo_all = min([R["arms"][a]["pooled_lo"] for a in arms] + [R["arms"][a]["cells"][str(b)]["lo"] for a in arms for b in sizes] + [0.3])
hi_all = max([R["arms"][a]["pooled_hi"] for a in arms] + [R["arms"][a]["cells"][str(b)]["hi"] for a in arms for b in sizes] + [1.2])
hi_all = min(hi_all, 1.6)
lo_all = max(lo_all, 0.3)
H = top + len(arms) * rowh + 60
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="11">',
     f'<rect width="{W}" height="{H}" fill="white"/>',
     '<text x="10" y="20" font-size="15" font-weight="bold">Plain rho selection round: group_ops, arm / base (paired, lower is better)</text>',
     f'<text x="10" y="38" fill="#444">points: ratio of sums; bars: Bonferroni bootstrap interval over curves ({R["comparisons"]} comparisons); dashed line: 1.0; * criteria met</text>']
def X(v, p):
    v = max(lo_all, min(hi_all, v))
    return left + p * pw + 10 + (v - lo_all) / (hi_all - lo_all) * (pw - 20)
for p, name in enumerate(panels):
    x0 = left + p * pw
    o.append(f'<text x="{x0 + pw / 2:.0f}" y="{top - 12}" text-anchor="middle" font-weight="bold">{"pooled" if name == "pooled" else name + " bits"}</text>')
    o.append(f'<line x1="{X(1, p):.1f}" y1="{top - 4}" x2="{X(1, p):.1f}" y2="{top + len(arms) * rowh}" stroke="#888" stroke-dasharray="3,3"/>')
    for t in (0.5, 1.5):
        if lo_all <= t <= hi_all:
            o.append(f'<text x="{X(t, p):.1f}" y="{top + len(arms) * rowh + 14}" text-anchor="middle" fill="#666">{t}</text>')
for i, a in enumerate(arms):
    y = top + i * rowh + 11
    r = R["arms"][a]
    o.append(f'<text x="{left - 8}" y="{y + 4}" text-anchor="end">{a}{" *" if r["winner_criteria_met"] else ""}</text>')
    for p, name in enumerate(panels):
        c = (r["pooled"], r["pooled_lo"], r["pooled_hi"]) if name == "pooled" else (
            r["cells"][name]["ratio"], r["cells"][name]["lo"], r["cells"][name]["hi"])
        col = "#2a6f97" if c[2] < 1 else ("#d1495b" if c[1] > 1 else "#777")
        o.append(f'<line x1="{X(c[1], p):.1f}" y1="{y}" x2="{X(c[2], p):.1f}" y2="{y}" stroke="{col}" stroke-width="2"/>')
        o.append(f'<circle cx="{X(c[0], p):.1f}" cy="{y}" r="3.2" fill="{col}"/>')
o.append("</svg>")
(HERE / "selection.svg").write_text("\n".join(o))
print("wrote selection.svg")
