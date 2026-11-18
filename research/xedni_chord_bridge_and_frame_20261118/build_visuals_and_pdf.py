#!/usr/bin/env python3
"""Generate quantitative SVG plot and compact (<64 KiB) vector PDF report."""

from __future__ import annotations

import json
from pathlib import Path
import zlib


HERE = Path(__file__).resolve().parent


def write_height_scaling_svg(panel_data: dict, frame_data: dict, out_path: Path) -> None:
    w, h = 920, 420
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-family="Helvetica, Arial, sans-serif">',
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="#ffffff"/>',
        # Panel A: Bar chart of Nov 17 certified relations by r
        '<text x="225" y="28" text-anchor="middle" font-size="13" font-weight="bold" fill="#0f172a">'
        'A. Nov 17 Panel Certified Relations by Rank (n = 1,205 ok rows)</text>',
        '<text x="225" y="45" text-anchor="middle" font-size="10.5" fill="#475569">'
        '66/67 overall (58/58 at r=7..9) are pre-lift Z^2 collinear triples [pcc:unverified]</text>',
    ]

    ax_x0, ax_y0, ax_w, ax_h = 65, 340, 330, 260
    lines.append(f'<line x1="{ax_x0}" y1="{ax_y0}" x2="{ax_x0 + ax_w}" y2="{ax_y0}" stroke="#334155" stroke-width="1.2"/>')
    lines.append(f'<line x1="{ax_x0}" y1="{ax_y0 - ax_h}" x2="{ax_x0}" y2="{ax_y0}" stroke="#334155" stroke-width="1.2"/>')

    max_y_a = 28
    for yv in (0, 5, 10, 15, 20, 25):
        yp = ax_y0 - (yv / max_y_a) * ax_h
        lines.append(f'<line x1="{ax_x0 - 4}" y1="{yp:.1f}" x2="{ax_x0 + ax_w}" y2="{yp:.1f}" stroke="#e2e8f0" stroke-width="1"/>')
        lines.append(f'<text x="{ax_x0 - 8}" y="{yp + 3.5:.1f}" text-anchor="end" font-size="10" fill="#334155">{yv}</text>')

    lines.append(
        f'<text x="22" y="{ax_y0 - ax_h / 2:.1f}" text-anchor="middle" font-size="10.5" fill="#334155" '
        f'transform="rotate(-90 22 {ax_y0 - ax_h / 2:.1f})">Certified relation count</text>'
    )

    by_r = panel_data["by_r"]
    for idx, r_val in enumerate(("6", "7", "8", "9")):
        row = by_r[r_val]
        col_c = row["collinear_certified"]
        cub_c = row["cubic_dependent_certified"]
        elig = row["eligible"]
        cx = ax_x0 + 48 + idx * 78
        bw = 42
        h_col = (col_c / max_y_a) * ax_h
        h_cub = (cub_c / max_y_a) * ax_h
        lines.append(
            f'<rect x="{cx - bw/2:.1f}" y="{ax_y0 - h_col:.1f}" width="{bw}" height="{h_col:.1f}" fill="#ef4444" opacity="0.88"/>'
        )
        if cub_c > 0:
            lines.append(
                f'<rect x="{cx - bw/2:.1f}" y="{ax_y0 - h_col - h_cub:.1f}" width="{bw}" height="{h_cub:.1f}" fill="#2563eb"/>'
            )
        tot = col_c + cub_c
        lbl = f"{col_c}+{cub_c}" if cub_c else f"{col_c}/0"
        lines.append(
            f'<text x="{cx:.1f}" y="{ax_y0 - (tot / max_y_a) * ax_h - 6:.1f}" text-anchor="middle" font-size="9.5" font-weight="bold" fill="#0f172a">{lbl}</text>'
        )
        lines.append(
            f'<text x="{cx:.1f}" y="{ax_y0 + 16}" text-anchor="middle" font-size="10.5" fill="#0f172a">r = {r_val}</text>'
        )
        lines.append(
            f'<text x="{cx:.1f}" y="{ax_y0 + 30}" text-anchor="middle" font-size="9" fill="#64748b">(n={elig})</text>'
        )

    # Legend A
    lines.append('<rect x="80" y="64" width="11" height="11" fill="#ef4444" opacity="0.88"/>')
    lines.append('<text x="96" y="73.5" font-size="9.5" fill="#1e293b">Pre-lift Z^2 collinear alias (det = 0)</text>')
    lines.append('<rect x="80" y="80" width="11" height="11" fill="#2563eb"/>')
    lines.append('<text x="96" y="89.5" font-size="9.5" fill="#1e293b">Cubic-dependent relation (1 row at p=31, r=6)</text>')

    # Panel B: r=9 coefficient bit-length scaling vs log2(p)
    bx_x0, bx_y0, bx_w, bx_h = 495, 340, 395, 260
    lines.append(
        '<text x="692" y="28" text-anchor="middle" font-size="13" font-weight="bold" fill="#0f172a">'
        'B. r = 9 Cubic Coefficient Height vs Field Bit-Length</text>'
    )
    lines.append(
        '<text x="692" y="45" text-anchor="middle" font-size="10.5" fill="#475569">'
        'Deterministic controls on y^2 = x^3 + 3x + 5 (6 primes, Rust/Python parity)</text>'
    )
    lines.append(f'<line x1="{bx_x0}" y1="{bx_y0}" x2="{bx_x0 + bx_w}" y2="{bx_y0}" stroke="#334155" stroke-width="1.2"/>')
    lines.append(f'<line x1="{bx_x0}" y1="{bx_y0 - bx_h}" x2="{bx_x0}" y2="{bx_y0}" stroke="#334155" stroke-width="1.2"/>')

    min_x, max_x = 5.0, 30.0
    max_y_b = 560.0
    for yv in (0, 100, 200, 300, 400, 500):
        yp = bx_y0 - (yv / max_y_b) * bx_h
        lines.append(f'<line x1="{bx_x0 - 4}" y1="{yp:.1f}" x2="{bx_x0 + bx_w}" y2="{yp:.1f}" stroke="#e2e8f0" stroke-width="1"/>')
        lines.append(f'<text x="{bx_x0 - 8}" y="{yp + 3.5:.1f}" text-anchor="end" font-size="10" fill="#334155">{yv}</text>')

    for xv in (6, 8, 12, 16, 20, 28):
        xp = bx_x0 + ((xv - min_x) / (max_x - min_x)) * bx_w
        lines.append(f'<line x1="{xp:.1f}" y1="{bx_y0}" x2="{xp:.1f}" y2="{bx_y0 + 4}" stroke="#334155" stroke-width="1"/>')
        lines.append(f'<text x="{xp:.1f}" y="{bx_y0 + 17}" text-anchor="middle" font-size="10" fill="#334155">{xv}</text>')

    lines.append(f'<text x="{bx_x0 + bx_w / 2:.1f}" y="{bx_y0 + 36}" text-anchor="middle" font-size="10.5" fill="#334155">Prime modulus size log2(p) [bits]</text>')
    lines.append(
        f'<text x="452" y="{bx_y0 - bx_h / 2:.1f}" text-anchor="middle" font-size="10.5" fill="#334155" '
        f'transform="rotate(-90 452 {bx_y0 - bx_h / 2:.1f})">Cubic max coefficient height [bits]</text>'
    )

    last_r = frame_data["r9_scaling_rows"][-1]
    series = [
        ("naive_affine_congruence", f"Naive Z=1 + affine mod p ({last_r['naive_affine_congruence']['coef_bits_per_log2_p']:.1f}x)", "#dc2626"),
        ("jksst_1frame_affine_points", f"JKSST 1-frame + Z=1 pts ({last_r['jksst_1frame_affine_points']['coef_bits_per_log2_p']:.1f}x)", "#d97706"),
        ("jksst_1frame_projective_lll", f"JKSST 1-frame + 3D-LLL ({last_r['jksst_1frame_projective_lll']['coef_bits_per_log2_p']:.1f}x)", "#0284c7"),
        ("jksst_126frames_projective_lll", f"JKSST 126-frame + 3D-LLL ({last_r['jksst_126frames_projective_lll']['coef_bits_per_log2_p']:.1f}x)", "#059669"),
    ]
    rows = frame_data["r9_scaling_rows"]
    for s_idx, (key, label, color) in enumerate(series):
        pts_svg = []
        for r in rows:
            xp = bx_x0 + ((r["log2_p"] - min_x) / (max_x - min_x)) * bx_w
            yp = bx_y0 - (r[key]["coefficient_bits"] / max_y_b) * bx_h
            pts_svg.append((xp, yp, r[key]["coefficient_bits"]))
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in pts_svg)
        lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.2" points="{poly}"/>')
        for x, y, _ in pts_svg:
            lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="{color}"/>')
        # Endpoint value label at p=28 bits
        lx, ly, lv = pts_svg[-1]
        lines.append(f'<text x="{lx + 6:.1f}" y="{ly + 3.5:.1f}" font-size="9.5" font-weight="bold" fill="{color}">{lv}b</text>')
        # Legend entry
        leg_y = 66 + s_idx * 16
        lines.append(f'<line x1="508" y1="{leg_y}" x2="526" y2="{leg_y}" stroke="{color}" stroke-width="2.4"/>')
        lines.append(f'<circle cx="517" cy="{leg_y}" r="3" fill="{color}"/>')
        lines.append(f'<text x="532" y="{leg_y + 3.5}" font-size="9.5" fill="#1e293b">{label}</text>')

    lines.append(
        '<text x="460" y="406" text-anchor="middle" font-size="9.5" fill="#64748b">'
        'Source: PANEL_DECOMPOSITION.json &amp; FRAME_CONTROL.json (commit-bound controls; not an ECDLP timing claim) [pcc:unverified]</text>'
    )
    lines.append("</svg>\n")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_vector_pdf(panel_data: dict, frame_data: dict, out_path: Path) -> None:
    """Build a crisp 2-page US-Letter vector PDF (< 35 KiB) with tables and embedded plots."""
    page_w, page_h = 612, 792
    pages_ops: list[str] = []

    # ---- PAGE 1: Title, Summary, Nov 17 Forensic Table, Lean Proof Map ----
    p1: list[str] = []

    def text1(x: float, y: float, size: float, font: str, s: str, rgb=(0.06, 0.09, 0.16)) -> None:
        p1.append(f"{rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} rg BT /{font} {size:.1f} Tf {x:.1f} {y:.1f} Td ({_pdf_escape(s)}) Tj ET")

    text1(48, 744, 14.5, "F2", "Xedni Plane-Cubic Chord-Origin Lead: Bridge, Collinearity Audit & JKSST Lift")
    text1(48, 727, 9.5, "F1", "Date: 2026-11-18  |  Status: Lean 4.35/Mathlib bridge checked; Nov 17 panel audited; JKSST lift in ca-icx [pcc:unverified]", (0.28, 0.33, 0.41))
    p1.append("0.75 0.78 0.82 RG 0.8 w 48 719 m 564 719 l S")

    y = 701
    summary_lines = [
        ("F2", 10.5, "1. Executive Findings [pcc:unverified]"),
        ("F1", 9.3, "- Forensic decomposition of the immutable Nov 17 r=6..9 panel (1,600 rows; 1,205 ok; 67 certified relations):"),
        ("F1", 9.3, "  transporting each origin-local relation n to fixed-flex coordinates r = n + S*e_u + S*e_v shows that"),
        ("F1", 9.3, "  66 / 67 (98.5%) overall -- and 58 / 58 (100.0%) across all new r = 7, 8, 9 regimes -- are pre-lift Z^2"),
        ("F1", 9.3, "  collinear point triples det(P_a, P_b, P_c) = 0 that hold on every smooth cubic by Bezout's theorem."),
        ("F1", 9.3, "- Only 1 / 67 row (p=31, generic, balanced, r=6, idx=9) is a genuine cubic-dependent relation; 0 / 1,205"),
        ("F1", 9.3, "  eligible rows contain an irreducible 6-point integer conic. Chord-origin coordinates disguised weight-3"),
        ("F1", 9.3, "  line divisors P_a+P_b+P_c ~ H ~ P_u+P_v+O as weight-5 vectors n = e_a+e_b+e_c-e_u-e_v."),
        ("F1", 9.3, "- Why r=7..9 yielded zero non-collinear cubic relations: naive Z=1 lifting + affine congruence c = 1*c_src"),
        ("F1", 9.3, "  (mod p) inflates unique r=9 cubics to ~18.6 log2(p) bits (105.5b median at p=251; 521b at 28-bit p)."),
        ("F1", 9.3, "- JKSST Steps 3-9 in suite/src/cryptanalysis/xedni_lift.rs (PGL_3(F_p) 4-point frame + 3D-LLL O(p^(2/3))"),
        ("F1", 9.3, "  projective point lift + homogeneous congruence) cuts r=9 cubic height to ~8.0 log2(p) bits (29b at p=251;"),
        ("F1", 9.3, "  223b at 28-bit p, saving 298 coefficient bits and 3,004 discriminant bits on fixed controls)."),
        ("F1", 9.3, "- Concrete good-reduction chord bridge proved in Lean 4.35.0-rc4 + Mathlib (16 theorems, 0 sorryAx)."),
    ]
    for fnt, sz, ln in summary_lines:
        if fnt == "F2":
            y -= 4
        text1(48, y, sz, fnt, ln)
        y -= 13.0

    y -= 6
    text1(48, y, 10.5, "F2", "2. Nov 17 Frozen Panel Decomposition (research/xedni_plane_group_20261117/run/rows.jsonl) [pcc:unverified]")
    y -= 14
    headers = ["Rank r", "C(r,3)", "Eligible", "Certified", "Z^2 Collinear", "Cubic-Dep.", "Med. Coef (p=251)", "Med. Disc (p=251)"]
    col_x = [48, 92, 138, 192, 250, 326, 392, 484]
    p1.append(f"0.93 0.95 0.98 rg 46 {y - 4:.1f} 520 14 re f")
    for cx, hd in zip(col_x, headers):
        text1(cx, y, 8.6, "F2", hd)
    y -= 14
    for r_str in ("6", "7", "8", "9"):
        rb = panel_data["by_r"][r_str]
        hs = panel_data["height_scaling"][f"r={r_str}/p=251/lift=balanced"]
        vals = [
            r_str,
            str(rb["point_triples_per_trial"]),
            str(rb["eligible"]),
            str(rb["certified"]),
            f"{rb['collinear_certified']} ({100.0 * rb['collinear_certified'] / rb['certified']:.1f}%)",
            str(rb["cubic_dependent_certified"]),
            f"{hs['median_coefficient_bits']:.1f} b",
            f"{hs['median_discriminant_bits']:.1f} b",
        ]
        for cx, vl in zip(col_x, vals):
            text1(cx, y, 8.6, "F1", vl)
        y -= 12.5
    p1.append(f"0.80 0.83 0.87 RG 0.6 w 46 {y + 8:.1f} m 566 {y + 8:.1f} l S")
    y -= 4
    text1(48, y, 8.6, "F2", "Total: 1,205 eligible | 67 certified | 66 Z^2 collinear aliases (98.5%) | 1 cubic-dependent (r=6, p=31) [pcc:unverified]")

    y -= 20
    text1(48, y, 10.5, "F2", "3. Kernel-Checked Lean 4.35 + Mathlib Bridge (GoodReductionChordBridge.lean) [pcc:unverified]")
    y -= 13.5
    lean_rows = [
        ("binaryRestriction_spec / chordRaw_on_cubic", "Exact JKSST ternary-to-binary cubic restriction & chord/tangent root vanishing"),
        ("chordRaw_map / smul / linear_equivariant", "Ring-hom reduction, mu*u^2*v^2 homogeneous scaling & GL_3 frame equivariance"),
        ("primitive_reduction_noncollapse", "V = g*O & phi(V) != 0 => phi(g) != 0 (automatic p does not divide gcd) & phi(O) != 0"),
        ("weierstrass_toAffine_chordRaw", "Maps chordRaw on WeierstrassCurve F to -(P1 + P2) in Mathlib W.toAffine.Point"),
        ("good_reduction_chord_origin_scalar", "Concrete bridge: reduced primitive chord origin equals -(m_j + m_k) * G on E(F)"),
        ("good_reduction_shifted_relation", "Composes reduced group relation to (sum_i n_i (m_i + m_j + m_k)) * G = 0"),
        ("origin_local_iff_fixed_transport", "Closes fixed-flex transport key r = n + S*e_u + S*e_v & 5-term collinear alias"),
    ]
    for thm, desc in lean_rows:
        text1(48, y, 8.2, "F3", thm, (0.18, 0.22, 0.58))
        text1(245, y, 8.3, "F1", desc)
        y -= 12.2

    # Pipeline diagram box at bottom of Page 1
    y -= 8
    text1(48, y, 10.5, "F2", "4. Pipeline & Divisor-Alias Diagram [pcc:unverified]")
    box_top = y - 8
    box_h = 128
    p1.append(f"0.97 0.98 0.99 rg 0.75 0.80 0.86 RG 0.8 w 48 {box_top - box_h:.1f} 516 {box_h} re B")
    nodes = [
        (60, box_top - 48, 114, 36, (0.88, 0.95, 0.99), "Source E(F_p)", "P_i = m_i G, P_r = t G"),
        (194, box_top - 48, 154, 36, (0.80, 0.98, 0.94), "JKSST PGL_3 + 3D-LLL", "4 frame pts + O(p^2/3) lifts"),
        (368, box_top - 48, 184, 36, (0.88, 0.91, 1.00), "Homogeneous Cubic + Bridge", "c = mu*c'_src; O -> -(m_j+m_k)G"),
        (194, box_top - 112, 358, 44, (1.00, 0.91, 0.91), "Nov 17 Naive Z=1 Audit Warning", "det(P_a,P_b,P_c)=0 aliases -> n = e_a+e_b+e_c-e_u-e_v (66/67 rows)"),
    ]
    for nx, ny, nw, nh, col, t_a, t_b in nodes:
        p1.append(f"{col[0]:.2f} {col[1]:.2f} {col[2]:.2f} rg 0.35 0.42 0.52 RG 0.7 w {nx} {ny} {nw} {nh} re B")
        text1(nx + 6, ny + nh - 13, 8.3, "F2", t_a)
        text1(nx + 6, ny + 7, 7.7, "F1", t_b, (0.20, 0.25, 0.33))
    # Arrows
    p1.append("0.25 0.30 0.38 RG 1.0 w 174 " + f"{box_top - 30:.1f} m 194 {box_top - 30:.1f} l S")
    p1.append("0.25 0.30 0.38 RG 1.0 w 348 " + f"{box_top - 30:.1f} m 368 {box_top - 30:.1f} l S")
    p1.append("0.75 0.25 0.25 RG 1.0 w 117 " + f"{box_top - 48:.1f} m 117 {box_top - 90:.1f} l 194 {box_top - 90:.1f} l S")

    text1(48, 34, 8.0, "F1", "Page 1 of 2  |  cryptanalysis:research/xedni_chord_bridge_and_frame_20261118/ [pcc:unverified]", (0.40, 0.45, 0.52))
    pages_ops.append("\n".join(p1))

    # ---- PAGE 2: JKSST Height-Scaling Controls, Vector Plot, Protocol & Boundaries ----
    p2: list[str] = []

    def text2(x: float, y: float, size: float, font: str, s: str, rgb=(0.06, 0.09, 0.16)) -> None:
        p2.append(f"{rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} rg BT /{font} {size:.1f} Tf {x:.1f} {y:.1f} Td ({_pdf_escape(s)}) Tj ET")

    text2(48, 744, 12.5, "F2", "5. Deterministic r = 9 Cubic Height Controls (y^2 = x^3 + 3x + 5, Rust/Python Parity) [pcc:unverified]")
    y = 724
    h2 = ["Prime p", "log2 p", "Naive Aff.", "Naive Hom.", "JKSST 1-Fr Z=1", "JKSST 1-Fr LLL", "JKSST 126-Fr LLL", "Disc. Bits (Aff -> J126)"]
    cx2 = [48, 106, 146, 200, 256, 328, 398, 468]
    p2.append(f"0.93 0.95 0.98 rg 46 {y - 4:.1f} 520 14 re f")
    for cx, hd in zip(cx2, h2):
        text2(cx, y, 8.0, "F2", hd)
    y -= 14
    for row in frame_data["r9_scaling_rows"]:
        na = row["naive_affine_congruence"]
        nh = row["naive_homogeneous_congruence"]
        f1a = row["jksst_1frame_affine_points"]
        f1l = row["jksst_1frame_projective_lll"]
        f126 = row["jksst_126frames_projective_lll"]
        vals = [
            str(row["p"]),
            f"{row['log2_p']:.1f}",
            f"{na['coefficient_bits']}b ({na['coef_bits_per_log2_p']:.1f}x)",
            f"{nh['coefficient_bits']}b",
            f"{f1a['coefficient_bits']}b ({f1a['coef_bits_per_log2_p']:.1f}x)",
            f"{f1l['coefficient_bits']}b ({f1l['coef_bits_per_log2_p']:.1f}x)",
            f"{f126['coefficient_bits']}b ({f126['coef_bits_per_log2_p']:.1f}x)",
            f"{na['discriminant_bits']} -> {f126['discriminant_bits']}b",
        ]
        for cx, vl in zip(cx2, vals):
            text2(cx, y, 8.0, "F1", vl)
        y -= 12.5
    p2.append(f"0.80 0.83 0.87 RG 0.6 w 46 {y + 8:.1f} m 566 {y + 8:.1f} l S")

    # Vector Quantitative Plot on Page 2
    plot_x0, plot_y0, plot_w, plot_h = 82, 430, 450, 175
    text2(82, plot_y0 + plot_h + 10, 9.8, "F2", "Quantitative Plot: r = 9 Max Cubic Coefficient Bits vs log2(p) (6 deterministic primes) [pcc:unverified]")
    p2.append(f"0.20 0.24 0.30 RG 0.9 w {plot_x0} {plot_y0} m {plot_x0 + plot_w} {plot_y0} l S")
    p2.append(f"0.20 0.24 0.30 RG 0.9 w {plot_x0} {plot_y0} m {plot_x0} {plot_y0 + plot_h} l S")
    for yv in (0, 150, 300, 450):
        yp = plot_y0 + (yv / 550.0) * plot_h
        p2.append(f"0.88 0.90 0.93 RG 0.5 w {plot_x0} {yp:.1f} m {plot_x0 + plot_w} {yp:.1f} l S")
        text2(plot_x0 - 24, yp - 3, 7.8, "F1", str(yv))
    for xv in (6, 8, 12, 16, 20, 28):
        xp = plot_x0 + ((xv - 5.0) / 25.0) * plot_w
        text2(xp - 5, plot_y0 - 11, 7.8, "F1", str(xv))
    text2(plot_x0 + 185, plot_y0 - 23, 8.2, "F1", "Field modulus bit-length log2(p)")

    last_r = frame_data["r9_scaling_rows"][-1]
    pdf_series = [
        ("naive_affine_congruence", (0.86, 0.15, 0.15), f"Naive Z=1 affine ({last_r['naive_affine_congruence']['coefficient_bits']}b @ 28b)"),
        ("jksst_1frame_affine_points", (0.85, 0.47, 0.02), f"JKSST 1-frame Z=1 ({last_r['jksst_1frame_affine_points']['coefficient_bits']}b @ 28b)"),
        ("jksst_1frame_projective_lll", (0.01, 0.52, 0.78), f"JKSST 1-frame 3D-LLL ({last_r['jksst_1frame_projective_lll']['coefficient_bits']}b @ 28b)"),
        ("jksst_126frames_projective_lll", (0.02, 0.59, 0.41), f"JKSST 126-frame 3D-LLL ({last_r['jksst_126frames_projective_lll']['coefficient_bits']}b @ 28b)"),
    ]
    for s_i, (key, col, lbl) in enumerate(pdf_series):
        pts_p = []
        for r in frame_data["r9_scaling_rows"]:
            xp = plot_x0 + ((r["log2_p"] - 5.0) / 25.0) * plot_w
            yp = plot_y0 + (r[key]["coefficient_bits"] / 550.0) * plot_h
            pts_p.append((xp, yp))
        p2.append(f"{col[0]:.2f} {col[1]:.2f} {col[2]:.2f} RG 1.5 w {pts_p[0][0]:.1f} {pts_p[0][1]:.1f} m " + " ".join(f"{x:.1f} {y:.1f} l" for x, y in pts_p[1:]) + " S")
        for x, y in pts_p:
            p2.append(f"{col[0]:.2f} {col[1]:.2f} {col[2]:.2f} rg {x - 2:.1f} {y - 2:.1f} 4 4 re f")
        ly = plot_y0 + plot_h - 14 - s_i * 12
        p2.append(f"{col[0]:.2f} {col[1]:.2f} {col[2]:.2f} RG 1.8 w {plot_x0 + 12} {ly + 3} m {plot_x0 + 26} {ly + 3} l S")
        text2(plot_x0 + 31, ly, 8.0, "F1", lbl, col)

    y = 386
    tail_lines = [
        ("F2", 10.5, "6. Claim Boundaries, Prospective Protocol & Checkpoint Gate [pcc:unverified]"),
        ("F1", 9.0, "- What is established: (a) machine-checked Lean 4 + Mathlib good-reduction chord bridge and fixed-flex"),
        ("F1", 9.0, "  divisor transport; (b) exact proof that 66/67 Nov 17 panel relations (58/58 at r=7..9) are pre-lift Z^2"),
        ("F1", 9.0, "  collinearities; (c) certified Rust/CLI implementation of JKSST PGL_3(F_p) + 3D-LLL + homogeneous cubic"),
        ("F1", 9.0, "  lifting cutting r=9 cubic height from ~18.6 log2(p) to ~8.0 log2(p) bits, with GL_3(Z) log-9 recovery."),
        ("F1", 9.0, "- Frame-line phenomenon: under JKSST PGL_3(F_p) + 3D-LLL, any mod-p collinear triple sharing two frame"),
        ("F1", 9.0, "  vertices maps to a coordinate/diagonal line (X=0, Y=0, Z=0, X=Y, ...) where 2D sublattice norm O(p^1/2)"),
        ("F1", 9.0, "  beats O(p^2/3), converting mod-p collinear triples (O(r^3/p)) into Z-collinear lifts deterministically."),
        ("F1", 9.0, "  Those events remain O(1/p) finite-field triple coincidences and do not speed up ECDLP."),
        ("F1", 9.0, "- What is NOT established: no new natural-lift experiment row was run (scripts/checkpoint.sh gate has no"),
        ("F1", 9.0, "  S3 upload token/profile in this container; tracked in problems/xedni-affine-cvp-checkpoint-access.md)."),
        ("F1", 9.0, "  Lowering cubic height from ~18.6 log2(p) to ~8.0 log2(p) does not overturn the conditional JKSST /"),
        ("F1", 9.0, "  Theorem X O(|M|/q) per-trial barrier or beat Pollard rho. PROTOCOL.md specifies the fresh-seed paired"),
        ("F1", 9.0, "  JKSST non-collinear panel and selected-lift canonical-height measurement to run once checkpointed."),
        ("F2", 9.5, "Sources: JKSST (DCC 2000); Silverman (DCC 2000); Fisher (PLMS 2008); Wu (arXiv:2610.00029v1). [pcc:unverified]"),
    ]
    for fnt, sz, ln in tail_lines:
        if fnt == "F2":
            y -= 4
        text2(48, y, sz, fnt, ln)
        y -= 12.6

    text2(48, 34, 8.0, "F1", "Page 2 of 2  |  All claims carry [pcc:unverified] producer standing pending CI verification.", (0.40, 0.45, 0.52))
    pages_ops.append("\n".join(p2))

    # Assemble minimal valid PDF 1.4 with FlateDecode streams
    objects: list[bytes] = []

    def add_obj(body: bytes) -> int:
        objects.append(body)
        return len(objects)

    font1 = add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    font2 = add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    font3 = add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

    content_ids = []
    for ops in pages_ops:
        comp = zlib.compress(ops.encode("latin-1"))
        cid = add_obj(
            f"<< /Length {len(comp)} /Filter /FlateDecode >>\nstream\n".encode("ascii")
            + comp
            + b"\nendstream"
        )
        content_ids.append(cid)

    pages_placeholder_idx = len(objects)
    objects.append(b"")  # placeholder for /Pages
    pages_obj_num = pages_placeholder_idx + 1

    page_ids = []
    for cid in content_ids:
        pid = add_obj(
            f"<< /Type /Page /Parent {pages_obj_num} 0 R /MediaBox [0 0 {page_w} {page_h}] "
            f"/Resources << /Font << /F1 {font1} 0 R /F2 {font2} 0 R /F3 {font3} 0 R >> >> "
            f"/Contents {cid} 0 R >>".encode("ascii")
        )
        page_ids.append(pid)

    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects[pages_placeholder_idx] = (
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii")
    )
    catalog_id = add_obj(f"<< /Type /Catalog /Pages {pages_obj_num} 0 R >>".encode("ascii"))

    buf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(buf))
        buf.extend(f"{idx} 0 obj\n".encode("ascii"))
        buf.extend(obj)
        buf.extend(b"\nendobj\n")
    xref_pos = len(buf)
    buf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    buf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        buf.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    buf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n".encode("ascii")
    )
    out_path.write_bytes(bytes(buf))


def main() -> None:
    panel_data = json.loads((HERE / "PANEL_DECOMPOSITION.json").read_text(encoding="utf-8"))
    frame_data = json.loads((HERE / "FRAME_CONTROL.json").read_text(encoding="utf-8"))
    svg_path = HERE / "height_scaling.svg"
    pdf_path = HERE / "xedni_chord_bridge_and_frame_20261118.pdf"
    write_height_scaling_svg(panel_data, frame_data, svg_path)
    write_vector_pdf(panel_data, frame_data, pdf_path)
    pdf_bytes = pdf_path.stat().st_size
    assert pdf_bytes < 64 * 1024, f"PDF exceeds 64 KiB artifact threshold: {pdf_bytes}"
    print(
        json.dumps(
            {
                "svg_bytes": svg_path.stat().st_size,
                "pdf_bytes": pdf_bytes,
                "under_64kib": pdf_bytes < 65536,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
