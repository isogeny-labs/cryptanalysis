#!/usr/bin/env python3
"""pairs.svg: per-pair wall-time ratio main / c = 12 (above 1 = change faster), Tier 1
(GitHub Actions run 40039118727) beside the exploratory authoring-VM run."""
import json
import random
import statistics as S
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPL = json.load(open(HERE / "summary_exploratory_local.json"))
T1 = json.load(open(HERE / "tier1-github-40039118727" / "pairs_summary.json"))
RUNS = {f: json.load(open(HERE / "tier1-github-40039118727" / f"run-summary_{f}.json"))["summary"] for f in ("j1728", "j0")}
W, H, x0, top, base = 860, 360, 70, 70, 290
lo, hi = 0.90, 1.15
y = lambda v: base - (min(max(v, lo), hi) - lo) / (hi - lo) * (base - top)
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="12">', f'<rect width="{W}" height="{H}" fill="white"/>',
     '<text x="10" y="22" font-size="15" font-weight="bold">Wall-time ratio per pair, main / c = 12 (above 1 = the change is faster)</text>',
     '<text x="10" y="42" fill="#444">15 alternating pairs per family on frozen 400-target panels (28–34 bits); bar: median, band: 95% interval</text>']
for t in (0.90, 0.95, 1.0, 1.05, 1.10, 1.15):
    o.append(f'<line x1="{x0}" x2="{W - 20}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="{"#888" if abs(t - 1) < 1e-9 else "#e3e3e3"}"/><text x="{x0 - 6}" y="{y(t) + 4:.1f}" text-anchor="end">{t:.2f}</text>')
cols = {"j1728": "#2a6f97", "j0": "#d1495b"}
slot = 0
for fam in ("j1728", "j0"):
    for label, ratios, ci, med in (
            ("Tier 1, GitHub Actions", T1[fam]["wall_ratios"], RUNS[fam]["bootstrap95_by_pair"], RUNS[fam]["observed_ratio_median"]),
            ("exploratory, authoring VM", EXPL[f"{fam}:online_ms"]["ratios"], EXPL[f"{fam}:online_ms"]["ci95"], EXPL[f"{fam}:online_ms"]["median_ref_over_cand"])):
        cx = x0 + 100 + slot * 185
        col = cols[fam]
        op = 1.0 if label.startswith("Tier") else 0.45
        o.append(f'<rect x="{cx - 55}" y="{y(ci[1]):.1f}" width="110" height="{max(1.5, y(ci[0]) - y(ci[1])):.1f}" fill="{col}" fill-opacity="{0.18 * op:.2f}"/>')
        o.append(f'<line x1="{cx - 55}" x2="{cx + 55}" y1="{y(med):.1f}" y2="{y(med):.1f}" stroke="{col}" stroke-width="2" stroke-opacity="{op}"/>')
        for j, r in enumerate(ratios):
            o.append(f'<circle cx="{cx - 45 + j * 90 / max(1, len(ratios) - 1):.1f}" cy="{y(r):.1f}" r="3" fill="{col}" fill-opacity="{op}"/>')
        o.append(f'<text x="{cx}" y="{base + 18}" text-anchor="middle" font-weight="bold">{fam}</text>')
        o.append(f'<text x="{cx}" y="{base + 32}" text-anchor="middle" font-size="10">{label}</text>')
        o.append(f'<text x="{cx}" y="{base + 46}" text-anchor="middle" font-size="10">{med:.3f} [{ci[0]:.3f}, {ci[1]:.3f}]</text>')
        slot += 1
o.append("</svg>")
(HERE / "pairs.svg").write_text("\n".join(o))
print("wrote pairs.svg")
