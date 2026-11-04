#!/usr/bin/env python3
"""Draw the frozen ratios of the n=83 field-ops run with their 95% intervals.

Reads run_github_41869146827/panel/result.json only; writes figures/result.svg.
A ratio above 1 means side B (field ops) is faster, except the A/A (near 1 by
design) and the planted control (the planted arm is slower by design).
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
RESULT = HERE / "run_github_41869146827" / "panel" / "result.json"
OUT = HERE / "figures" / "result.svg"
ROWS = [
    ("PRIMARY end to end, A / B", "primary_e2e_paired_A_over_B", "#167f73"),
    ("index build, A / B", "stage_secondary_index_build_A_over_B", "#637bad"),
    ("scan self-test, A / B", "stage_secondary_scan_selftest_A_over_B", "#637bad"),
    ("rank stage, A / B", "stage_secondary_rank_stage_A_over_B", "#637bad"),
    ("online, A / B", "stage_secondary_online_A_over_B", "#637bad"),
    ("cold process, A / B", "cold_A_over_B", "#637bad"),
    ("A/A end to end, B / Baa", "aa_e2e_B_over_Baa", "#93a1a4"),
    ("planted index build, X / B", "planted_index_build_cM38FOX_over_cM38FO", "#aa8b5b"),
]


def main():
    stats = json.loads(RESULT.read_text())["statistics"]
    W, left, right, top, row_h = 900, 270, 140, 70, 34
    lo, hi = 0.9, 2.9
    gw = W - left - right
    H = top + row_h * len(ROWS) + 60
    X = lambda v: left + (v - lo) / (hi - lo) * gw
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="Helvetica,Arial,sans-serif" font-size="13">',
         f'<rect width="{W}" height="{H}" fill="white"/>',
         f'<text x="20" y="28" font-size="16" font-weight="bold">n = 83 field ops, Tier 1 run 41869146827: '
         'frozen ratios, 95% two-stage paired bootstrap</text>',
         '<text x="20" y="48" fill="#555">ratio of sums over 36 primary pairs (12 points), 24 A/A pairs, '
         '12 planted pairs; AMD EPYC 9V74, one pinned CPU; above 1 = side B faster</text>']
    for k in range(0, 11):
        v = lo + (hi - lo) * k / 10
        o.append(f'<line x1="{X(v):.1f}" y1="{top - 8}" x2="{X(v):.1f}" y2="{top + row_h * len(ROWS)}" stroke="#eee"/>')
        o.append(f'<text x="{X(v):.1f}" y="{top + row_h * len(ROWS) + 18}" text-anchor="middle" fill="#555">{v:.1f}</text>')
    o.append(f'<line x1="{X(1):.1f}" y1="{top - 8}" x2="{X(1):.1f}" y2="{top + row_h * len(ROWS)}" '
             'stroke="#888" stroke-dasharray="5 4"/>')
    for i, (label, key, colour) in enumerate(ROWS):
        s = stats[key]
        y = top + row_h * i + row_h / 2
        est, (a, b) = s["estimate"], s["ci95"]
        o.append(f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end">{label}</text>')
        o.append(f'<line x1="{X(a):.1f}" y1="{y:.1f}" x2="{X(b):.1f}" y2="{y:.1f}" stroke="{colour}" stroke-width="3"/>')
        o.append(f'<circle cx="{X(est):.1f}" cy="{y:.1f}" r="5" fill="{colour}"/>')
        o.append(f'<text x="{W - right + 10}" y="{y + 4:.1f}" fill="#333">{est:.3f} [{a:.3f}, {b:.3f}]</text>')
    o.append(f'<text x="{left + gw / 2:.1f}" y="{top + row_h * len(ROWS) + 40}" text-anchor="middle" '
             'fill="#555">ratio (wall time, one host class)</text>')
    o.append("</svg>")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(o) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
