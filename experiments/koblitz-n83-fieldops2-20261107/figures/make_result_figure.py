#!/usr/bin/env python3
"""Draw the frozen ratios of the n=83 field-ops-2 run with their 95% intervals.

Usage: make_result_figure.py RUN_DIR   (RUN_DIR = run_github_<id>/)
Reads RUN_DIR/panel/result.json only; writes figures/result.svg. A ratio above
1 means side B (R1) is faster, except the A/A (near 1 by design) and the
planted control (the planted arm is slower by design).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from verify_receipt import PLANTED_KEY  # noqa: E402

OUT = HERE / "figures" / "result.svg"
ROWS = [
    ("PRIMARY end to end, A / B", "primary_e2e_paired_A_over_B", "#167f73"),
    ("index build, A / B", "stage_secondary_index_build_A_over_B", "#637bad"),
    ("scan self-test, A / B", "stage_secondary_scan_selftest_A_over_B", "#637bad"),
    ("rank stage, A / B", "stage_secondary_rank_stage_A_over_B", "#637bad"),
    ("online, A / B", "stage_secondary_online_A_over_B", "#637bad"),
    ("cold process, A / B", "cold_A_over_B", "#637bad"),
    ("A/A end to end, B / Baa", "aa_e2e_B_over_Baa", "#93a1a4"),
    ("planted index build, X / B", PLANTED_KEY, "#aa8b5b"),
]


def main():
    run = Path(sys.argv[1]).resolve()
    stats = json.loads((run / "panel" / "result.json").read_text())["statistics"]
    rows = [(label, key, colour) for label, key, colour in ROWS if key in stats]
    values = [v for _, key, _ in rows for v in (stats[key]["estimate"], *stats[key]["ci95"])]
    lo, hi = min(0.9, min(values) - 0.02), max(1.1, max(values) + 0.02)
    W, left, right, top, row_h = 900, 270, 140, 70, 34
    gw = W - left - right
    H = top + row_h * len(rows) + 60
    X = lambda v: left + (v - lo) / (hi - lo) * gw
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="Helvetica,Arial,sans-serif" font-size="13">',
         f'<rect width="{W}" height="{H}" fill="white"/>',
         f'<text x="20" y="28" font-size="16" font-weight="bold">n = 83 field ops 2 (R1), Tier 1 {run.name[11:]}: '
         'frozen ratios, 95% two-stage paired bootstrap</text>',
         '<text x="20" y="48" fill="#555">ratio of sums over 36 primary pairs (12 points), 24 A/A pairs, '
         '12 planted pairs; one pinned CPU; above 1 = side B faster</text>']
    for k in range(0, 11):
        v = lo + (hi - lo) * k / 10
        o.append(f'<line x1="{X(v):.1f}" y1="{top - 8}" x2="{X(v):.1f}" y2="{top + row_h * len(rows)}" stroke="#eee"/>')
        o.append(f'<text x="{X(v):.1f}" y="{top + row_h * len(rows) + 18}" text-anchor="middle" fill="#555">{v:.2f}</text>')
    o.append(f'<line x1="{X(1):.1f}" y1="{top - 8}" x2="{X(1):.1f}" y2="{top + row_h * len(rows)}" '
             'stroke="#888" stroke-dasharray="5 4"/>')
    for i, (label, key, colour) in enumerate(rows):
        s = stats[key]
        y = top + row_h * i + row_h / 2
        est, (a, b) = s["estimate"], s["ci95"]
        o.append(f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end">{label}</text>')
        o.append(f'<line x1="{X(a):.1f}" y1="{y:.1f}" x2="{X(b):.1f}" y2="{y:.1f}" stroke="{colour}" stroke-width="3"/>')
        o.append(f'<circle cx="{X(est):.1f}" cy="{y:.1f}" r="5" fill="{colour}"/>')
        o.append(f'<text x="{W - right + 10}" y="{y + 4:.1f}" fill="#333">{est:.4f} [{a:.4f}, {b:.4f}]</text>')
    o.append(f'<text x="{left + gw / 2:.1f}" y="{top + row_h * len(rows) + 40}" text-anchor="middle" '
             'fill="#555">ratio (wall time, one host class)</text>')
    o.append("</svg>")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(o) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
