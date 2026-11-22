#!/usr/bin/env python3
"""Draw the frozen ratios of the n=83 field-ops-2 (R1) vs field-ops on D4 run with their 95% intervals.

Usage: make_result_figure.py RUN_DIR   (RUN_DIR = run_github_<id>/)
Reads RUN_DIR/panel/result.json only; writes figures/result.svg and, with
Pillow, figures/result.png (the same layout drawn directly: this host has no
SVG rasterizer). A ratio above
1 means side B (R1) is faster, except the A/A (near 1 by design) and the
planted control (the planted arm is slower by design).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from verify_receipt import PLANTED_KEY  # noqa: E402  (planted_index_build_cD4R1X_over_cD4R1)

OUT = HERE / "figures" / "result.svg"
ROWS = [
    ("PRIMARY end to end, A / B", "primary_e2e_paired_A_over_B", "#167f73"),
    ("index build, A / B", "stage_secondary_index_build_A_over_B", "#637bad"),
    ("scan self-test, A / B", "stage_secondary_scan_selftest_A_over_B", "#637bad"),
    ("rank stage, A / B", "stage_secondary_rank_stage_A_over_B", "#637bad"),
    ("online, A / B", "stage_secondary_online_A_over_B", "#637bad"),
    ("cold process, A / B", "cold_A_over_B", "#637bad"),
    ("A/A end to end, B / Baa", "aa_e2e_B_over_Baa", "#93a1a4"),
    ("A/A cold, B / Baa", "aa_cold_B_over_Baa", "#93a1a4"),
    ("planted index build, X / B", PLANTED_KEY, "#aa8b5b"),
]


def main():
    run = Path(sys.argv[1]).resolve()
    stats = json.loads((run / "panel" / "result.json").read_text())["statistics"]
    rows = [(label, key, colour) for label, key, colour in ROWS if key in stats]
    values = []
    lo, hi = 0.9, 3.1
    W, left, right, top, row_h = 1010, 270, 250, 70, 34
    gw = W - left - right
    H = top + row_h * len(rows) + 60
    X = lambda v: left + (v - lo) / (hi - lo) * gw
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="Helvetica,Arial,sans-serif" font-size="13">',
         f'<rect width="{W}" height="{H}" fill="white"/>',
         f'<text x="20" y="28" font-size="16" font-weight="bold">n = 83 R1 vs field-ops, both on D4, Tier 1 {run.name[11:]}: '
         'frozen ratios, 95% two-stage paired bootstrap</text>',
         '<text x="20" y="48" fill="#555">ratio of sums over 36 primary pairs (12 points), 24 A/A pairs, '
         '12 planted pairs; one pinned CPU; above 1 = side B (R1) faster</text>']
    for k in range(0, 11):
        v = lo + (hi - lo) * k / 10
        o.append(f'<line x1="{X(v):.1f}" y1="{top - 8}" x2="{X(v):.1f}" y2="{top + row_h * len(rows)}" stroke="#eee"/>')
        o.append(f'<text x="{X(v):.1f}" y="{top + row_h * len(rows) + 18}" text-anchor="middle" fill="#555">{v:.1f}</text>')
    o.append(f'<line x1="{X(1):.1f}" y1="{top - 8}" x2="{X(1):.1f}" y2="{top + row_h * len(rows)}" '
             'stroke="#888" stroke-dasharray="5 4"/>')
    for i, (label, key, colour) in enumerate(rows):
        s = stats[key]
        y = top + row_h * i + row_h / 2
        est, (a, b) = s["estimate"], s["ci95"]
        o.append(f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end">{label}</text>')
        if True:
            o.append(f'<line x1="{X(a):.1f}" y1="{y:.1f}" x2="{X(b):.1f}" y2="{y:.1f}" stroke="{colour}" stroke-width="3"/>')
        if True:
            o.append(f'<circle cx="{X(est):.1f}" cy="{y:.1f}" r="5" fill="{colour}"/>')
        o.append(f'<text x="{W - right + 10}" y="{y + 4:.1f}" fill="#333">{est:.4f} [{a:.4f}, {b:.4f}]</text>')
    o.append(f'<text x="{left + gw / 2:.1f}" y="{top + row_h * len(rows) + 40}" text-anchor="middle" '
             'fill="#555">ratio (wall time, one host class)</text>')
    o.append("</svg>")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(o) + "\n")
    print(OUT)
    png(rows, stats, run, lo, hi, W, H, left, right, top, row_h, X)


def png(rows, stats, run, lo, hi, W, H, left, right, top, row_h, X):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return
    s = 1.5
    img = Image.new("RGB", (int(W * s), int(H * s)), "white")
    d = ImageDraw.Draw(img)
    regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    f, fb = ImageFont.truetype(regular, int(12 * s)), ImageFont.truetype(bold, int(15 * s))
    P = lambda x, y: (x * s, y * s)  # noqa: E731
    d.text(P(20, 14), "n = 83 R1 vs field-ops, both on D4, Tier 1 %s: frozen ratios, 95%% two-stage paired bootstrap" % run.name[11:], fill="black", font=fb)
    d.text(P(20, 38), "ratio of sums over 36 primary pairs (12 points), 24 A/A pairs, 12 planted pairs; one pinned CPU; above 1 = side B (R1) faster", fill="#555555", font=f)
    bottom = top + row_h * len(rows)
    for k in range(0, 11):
        v = lo + (hi - lo) * k / 10
        d.line([P(X(v), top - 8), P(X(v), bottom)], fill="#eeeeee")
        d.text(P(X(v) - 12, bottom + 8), "%.1f" % v, fill="#555555", font=f)
    for y in range(top - 8, bottom, 9):
        d.line([P(X(1), y), P(X(1), min(y + 5, bottom))], fill="#888888")
    for i, (label, key, colour) in enumerate(rows):
        est, (a, b) = stats[key]["estimate"], stats[key]["ci95"]
        y = top + row_h * i + row_h / 2
        w = d.textlength(label, font=f) / s
        d.text(P(left - 10 - w, y - 8), label, fill="black", font=f)
        if True:
            d.line([P(X(a), y), P(X(b), y)], fill=colour, width=int(3 * s))
            d.ellipse([P(X(est) - 5, y - 5), P(X(est) + 5, y + 5)], fill=colour)
        d.text(P(W - right + 10, y - 8), "%.4f [%.4f, %.4f]" % (est, a, b), fill="#333333", font=f)
    d.text(P(left + (W - left - right) / 2 - 90, bottom + 30), "ratio (wall time, one host class)", fill="#555555", font=f)
    img.convert("P", palette=Image.ADAPTIVE, colors=32).save(OUT.with_suffix(".png"), dpi=(150, 150), optimize=True)
    print(OUT.with_suffix(".png"))


if __name__ == "__main__":
    main()
