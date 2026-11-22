#!/usr/bin/env python3
"""pairs.svg from summary_exploratory_local.json: each pair's wall-time ratio (reference / candidate)."""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
S = json.load(open(HERE / "summary_exploratory_local.json"))
W, H, x0, top, base = 760, 330, 70, 70, 270
lo, hi = 0.85, 1.20
y = lambda v: base - (v - lo) / (hi - lo) * (base - top)
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="12">', f'<rect width="{W}" height="{H}" fill="white"/>',
     '<text x="10" y="22" font-size="15" font-weight="bold">Exploratory (untiered) wall-time ratio per pair: main / c = 12 (above 1 = change faster)</text>',
     '<text x="10" y="42" fill="#444">authoring VM, CPU 3 pinned, 15 alternating pairs per family, 400-target panels at 28–34 bits; bar: median, band: 95% bootstrap</text>']
for t in (0.9, 1.0, 1.1, 1.2):
    o.append(f'<line x1="{x0}" x2="{W - 20}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="{"#888" if t == 1 else "#e3e3e3"}"/><text x="{x0 - 6}" y="{y(t) + 4:.1f}" text-anchor="end">{t:.2f}</text>')
for i, (fam, col) in enumerate((("j1728", "#2a6f97"), ("j0", "#d1495b"))):
    e = S[f"{fam}:online_ms"]; cx = x0 + 160 + i * 320
    o.append(f'<rect x="{cx - 60}" y="{y(e["ci95"][1]):.1f}" width="120" height="{y(e["ci95"][0]) - y(e["ci95"][1]):.1f}" fill="{col}" fill-opacity="0.15"/>')
    o.append(f'<line x1="{cx - 60}" x2="{cx + 60}" y1="{y(e["median_ref_over_cand"]):.1f}" y2="{y(e["median_ref_over_cand"]):.1f}" stroke="{col}" stroke-width="2"/>')
    for j, r in enumerate(e["ratios"]):
        o.append(f'<circle cx="{cx - 50 + j * 100 / 14:.1f}" cy="{y(r):.1f}" r="3" fill="{col}"/>')
    o.append(f'<text x="{cx}" y="{base + 20}" text-anchor="middle">{fam}: median {e["median_ref_over_cand"]:.3f} [{e["ci95"][0]:.3f}, {e["ci95"][1]:.3f}]</text>')
o.append("</svg>")
(HERE / "pairs.svg").write_text("\n".join(o)); print("wrote pairs.svg")
