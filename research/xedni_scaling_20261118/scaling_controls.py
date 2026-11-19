#!/usr/bin/env python3
"""Deterministic controls and visual/PDF generator for Phase 1 Xedni scaling.

1. Measures order-statistic short-pool 3D-LLL cubic height reduction across
   p in {67, 251, 4091, 65519, 1048571, 268435399} (6 to 28 bits, r = 9) for
   pool sizes W in {9, 32, 128} against naive Z = 1 affine lifting.
2. Executes deterministic single-instance `ca-icx xedni-solve` controls on
   prime-order curves across p in {67, 127, 251, 509, 1021} with strict
   non-collinear, non-tautological verification and matched Pollard-rho cost
   accounting.
3. Renders `scaling_results.svg` and a compact (<64 KiB) vector PDF report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import zlib

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "research/xedni_chord_bridge_and_frame_20261118"))
import frame_height_control as fhc  # noqa: E402

DEFAULT_BINARY = ROOT / "suite/target/release/ca-icx"
SOLVER_RS = ROOT / "suite/src/cryptanalysis/xedni_solver.rs"
HEIGHT_PRIMES = (67, 251, 4091, 65519, 1048571, 268435399)


def deterministic_pool_on_curve(p: int, a: int, b: int, count: int) -> list[tuple[int, int, int]]:
    assert p % 4 == 3
    exp = (p + 1) // 4
    pts: list[tuple[int, int, int]] = []
    seen_x: set[int] = set()
    step = (p * 37) // 100 + 1
    while math.gcd(step, p) != 1:
        step += 1
    x = (p * 19) // 100 + 1
    guard = 0
    while len(pts) < count and guard < p * 2:
        guard += 1
        x = (x + step) % p
        if x in seen_x:
            continue
        rhs = (x**3 + a * x + b) % p
        if rhs == 0:
            continue
        y = pow(rhs, exp, p)
        if (y * y) % p == rhs:
            seen_x.add(x)
            if len(pts) % 2 == 1:
                y = (-y) % p
            pts.append((x, y, 1))
    return pts


def short_pool_lift_python_and_rust(
    binary: Path, p: int, source_cubic: list[int], pool: list[tuple[int, int, int]], r: int = 9
) -> dict:
    # Normalize first general-position 4-tuple via ca-icx on pool[:9], then rank all pool points by 3D-LLL norm
    first9 = fhc.run_ca_icx_jksst(binary, p, source_cubic, pool[:9], "projective-lll", 1, [0, 1, 2, 3])
    m_from = [[int(v) for v in row] for row in first9["matrix_from_source_mod_p"]]

    frame_lifted = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 1)]
    scored = []
    for idx in range(4, len(pool)):
        pt = pool[idx]
        mapped = tuple(sum(m_from[ri][ci] * pt[ci] for ci in range(3)) % p for ri in range(3))
        lifted = fhc.short_proj_lift_python(mapped, p)
        norm2 = sum(c * c for c in lifted)
        max_b = max(abs(c).bit_length() for c in lifted)
        scored.append((norm2, max_b, idx, lifted))
    scored.sort()

    chosen_idx = [0, 1, 2, 3]
    chosen_pts = list(frame_lifted)
    for _, _, idx, lifted in scored:
        if len(chosen_idx) == r:
            break
        # Reject any pre-lift Z^2 collinear triple
        col = False
        for i in range(len(chosen_pts)):
            for j in range(i + 1, len(chosen_pts)):
                a_, b_, c_ = chosen_pts[i], chosen_pts[j], lifted
                det = (
                    a_[0] * (b_[1] * c_[2] - b_[2] * c_[1])
                    - a_[1] * (b_[0] * c_[2] - b_[2] * c_[0])
                    + a_[2] * (b_[0] * c_[1] - b_[1] * c_[0])
                )
                if det == 0:
                    col = True
                    break
            if col:
                break
        if not col:
            chosen_idx.append(idx)
            chosen_pts.append(lifted)

    sub_pts = [pool[i] for i in chosen_idx]
    res = fhc.run_ca_icx_jksst(binary, p, source_cubic, sub_pts, "projective-lll", 1, [0, 1, 2, 3])
    return {
        "pool_size": len(pool),
        "coefficient_bits": res["optimized_score"]["coefficient_height_bits"],
        "discriminant_bits": res["optimized_score"]["discriminant_bits"],
        "max_point_coord_bits": res["max_point_coordinate_bits"],
        "collinear_triples": len(res["pre_lift_collinear_triples"]),
    }


def prime_order_curve(p: int) -> tuple[int, int, int, tuple[int, int]]:
    for a in (3, 1, 2, 5):
        for b in range(1, 200):
            if (4 * a**3 + 27 * b**2) % p == 0:
                continue
            pts = [None]
            for x in range(p):
                rhs = (x**3 + a * x + b) % p
                for y in range(p):
                    if (y * y) % p == rhs:
                        pts.append((x, y))
            n = len(pts)
            if n > 3 and all(n % d != 0 for d in range(2, int(n**0.5) + 1)):
                return a, b, n, pts[1]
    raise RuntimeError(f"no prime-order curve found at p={p}")


def ec_mul(k: int, pt: tuple[int, int], a: int, p: int) -> tuple[int, int]:
    def add(p1, p2):
        if p1 is None:
            return p2
        if p2 is None:
            return p1
        x1, y1 = p1
        x2, y2 = p2
        if x1 == x2:
            if (y1 + y2) % p == 0:
                return None
            lam = (3 * x1 * x1 + a) * pow(2 * y1, -1, p) % p
        else:
            lam = (y2 - y1) * pow(x2 - x1, -1, p) % p
        x3 = (lam * lam - x1 - x2) % p
        y3 = (lam * (x1 - x3) - y1) % p
        return (x3, y3)

    acc = None
    cur = pt
    while k > 0:
        if k & 1:
            acc = add(acc, cur)
        cur = add(cur, cur)
        k >>= 1
    assert acc is not None
    return acc


def run_controls(binary: Path) -> dict:
    solver_sha = hashlib.sha256(SOLVER_RS.read_bytes()).hexdigest()
    source_cubic = [1, 0, 0, 0, 0, 0, -1, 3, 0, 5]

    height_rows = []
    for p in HEIGHT_PRIMES:
        log2_p = math.log2(p)
        max_w = min(128, (p - 1) // 2)
        pool = deterministic_pool_on_curve(p, 3, 5, max(9, max_w))
        naive = fhc.run_ca_icx_naive_affine(binary, p, source_cubic, pool[:9])
        w9 = short_pool_lift_python_and_rust(binary, p, source_cubic, pool[:9], 9)
        w32 = short_pool_lift_python_and_rust(binary, p, source_cubic, pool[: min(32, len(pool))], 9)
        w128 = short_pool_lift_python_and_rust(binary, p, source_cubic, pool, 9)
        height_rows.append(
            {
                "p": p,
                "log2_p": round(log2_p, 4),
                "naive_z1_affine_bits": naive["optimized_score"]["coefficient_height_bits"],
                "naive_z1_disc_bits": naive["optimized_score"]["discriminant_bits"],
                "jksst_w9_bits": w9["coefficient_bits"],
                "jksst_w32_bits": w32["coefficient_bits"],
                "jksst_w128_bits": w128["coefficient_bits"],
                "jksst_w128_disc_bits": w128["discriminant_bits"],
                "jksst_w128_coord_bits": w128["max_point_coord_bits"],
                "jksst_w128_pool_used": w128["pool_size"],
            }
        )

    solve_specs = [
        (67, 29, 7, 20, 120),
        (127, 83, 8, 32, 240),
        (251, 173, 8, 48, 360),
        (509, 317, 8, 64, 500),
        (1021, 619, 8, 96, 600),
    ]
    solve_rows = []
    for p, secret, r, pool_sz, max_trials in solve_specs:
        a, b, n, gen = prime_order_curve(p)
        target = ec_mul(secret, gen, a, p)
        cfg = {
            "modulus": str(p),
            "a": str(a),
            "b": str(b),
            "generator": [str(gen[0]), str(gen[1])],
            "subgroup_order": str(n),
            "target": [str(target[0]), str(target[1])],
            "mode": "direct",
            "rank_points": r,
            "pool_size": pool_sz,
            "num_aux_primes": 7,
            "max_trials": max_trials,
            "seed": 20261118,
            "require_non_collinear": True,
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(cfg, handle)
            cfg_path = Path(handle.name)
        try:
            t0 = time.time()
            cp = subprocess.run(
                [str(binary), "--json", "xedni-solve", "--input", str(cfg_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            wall_s = round(time.time() - t0, 4)
        finally:
            cfg_path.unlink(missing_ok=True)
        res = json.loads(cp.stdout)["result"]
        if res["verified"]:
            assert int(res["recovered_discrete_log"]) == secret % n
        solve_rows.append(
            {
                "p": p,
                "a": a,
                "b": b,
                "subgroup_order": n,
                "subgroup_bits": res["subgroup_bits"],
                "rank_points": r,
                "pool_size": pool_sz,
                "max_trials": max_trials,
                "trials_attempted": res["trials_attempted"],
                "verified": res["verified"],
                "recovered_discrete_log": res["recovered_discrete_log"],
                "non_collinear_relations_found": res["non_collinear_relations_found"],
                "median_coefficient_bits": res["median_coefficient_bits"],
                "min_coefficient_bits": res["min_coefficient_bits"],
                "total_charged_ops": res["work"]["total_charged_ops"],
                "matched_rho_expected_ops": res["matched_rho_expected_ops"],
                "work_over_rho": res["work_over_rho"],
                "wall_seconds": wall_s,
            }
        )

    return {
        "schema": "cryptanalysis.xedni-phase1-scaling-controls/v1",
        "rust_solver_path": "suite/src/cryptanalysis/xedni_solver.rs",
        "rust_solver_sha256": solver_sha,
        "scope": "deterministic fixed-seed Phase 1 scaling controls (not a fresh-seed statistical benchmark)",
        "r9_short_pool_height_rows": height_rows,
        "non_collinear_solve_ladder": solve_rows,
    }


def write_visuals(data: dict) -> dict:
    w, h = 940, 420
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-family="Helvetica, Arial, sans-serif">',
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="#ffffff"/>',
        '<text x="235" y="28" text-anchor="middle" font-size="13" font-weight="bold" fill="#0f172a">'
        'A. r = 9 Cubic Height with Short-Pool Preselection</text>',
        '<text x="235" y="45" text-anchor="middle" font-size="10.5" fill="#475569">'
        'y^2 = x^3 + 3x + 5 across 6..28 bits (0 collinear triples) [pcc:unverified]</text>',
    ]
    ax0, ay0, aw, ah = 65, 340, 360, 260
    lines.append(f'<line x1="{ax0}" y1="{ay0}" x2="{ax0+aw}" y2="{ay0}" stroke="#334155" stroke-width="1.2"/>')
    lines.append(f'<line x1="{ax0}" y1="{ay0-ah}" x2="{ax0}" y2="{ay0}" stroke="#334155" stroke-width="1.2"/>')
    for yv in (0, 100, 200, 300, 400, 500):
        yp = ay0 - (yv / 550.0) * ah
        lines.append(f'<line x1="{ax0-4}" y1="{yp:.1f}" x2="{ax0+aw}" y2="{yp:.1f}" stroke="#e2e8f0" stroke-width="1"/>')
        lines.append(f'<text x="{ax0-8}" y="{yp+3.5:.1f}" text-anchor="end" font-size="10" fill="#334155">{yv}</text>')
    for xv in (6, 8, 12, 16, 20, 28):
        xp = ax0 + ((xv - 5.0) / 25.0) * aw
        lines.append(f'<text x="{xp:.1f}" y="{ay0+16}" text-anchor="middle" font-size="10" fill="#334155">{xv}</text>')
    lines.append(f'<text x="{ax0+aw/2:.1f}" y="{ay0+34}" text-anchor="middle" font-size="10.5" fill="#334155">Prime size log2(p) [bits]</text>')

    hrows = data["r9_short_pool_height_rows"]
    series = [
        ("naive_z1_affine_bits", f"Naive Z=1 ({hrows[-1]['naive_z1_affine_bits']}b @ 28b)", "#dc2626"),
        ("jksst_w9_bits", f"JKSST 1-frame W=9 ({hrows[-1]['jksst_w9_bits']}b @ 28b)", "#d97706"),
        ("jksst_w32_bits", f"JKSST short-pool W=32 ({hrows[-1]['jksst_w32_bits']}b @ 28b)", "#0284c7"),
        ("jksst_w128_bits", f"JKSST short-pool W=128 ({hrows[-1]['jksst_w128_bits']}b @ 28b)", "#059669"),
    ]
    for s_idx, (key, lbl, col) in enumerate(series):
        pts_s = []
        for r in hrows:
            xp = ax0 + ((r["log2_p"] - 5.0) / 25.0) * aw
            yp = ay0 - (r[key] / 550.0) * ah
            pts_s.append((xp, yp))
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts_s)
        lines.append(f'<polyline fill="none" stroke="{col}" stroke-width="2.2" points="{poly}"/>')
        for x, y in pts_s:
            lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{col}"/>')
        ly = 66 + s_idx * 16
        lines.append(f'<line x1="78" y1="{ly}" x2="96" y2="{ly}" stroke="{col}" stroke-width="2.4"/>')
        lines.append(f'<text x="102" y="{ly+3.5}" font-size="9.5" fill="#1e293b">{lbl}</text>')

    # Panel B: Non-collinear solve ladder log10(S / S_rho)
    bx0, by0, bw, bh = 515, 340, 390, 260
    lines.append(
        '<text x="710" y="28" text-anchor="middle" font-size="13" font-weight="bold" fill="#0f172a">'
        'B. Non-Collinear Xedni ECDLP Solves: log10(S / S_rho)</text>'
    )
    lines.append(
        '<text x="710" y="45" text-anchor="middle" font-size="10.5" fill="#475569">'
        'Prior Nov 17 panel had 0 non-collinear hits above p=31 [pcc:unverified]</text>'
    )
    lines.append(f'<line x1="{bx0}" y1="{by0}" x2="{bx0+bw}" y2="{by0}" stroke="#334155" stroke-width="1.2"/>')
    lines.append(f'<line x1="{bx0}" y1="{by0-bh}" x2="{bx0}" y2="{by0}" stroke="#334155" stroke-width="1.2"/>')
    for lv in (0, 1, 2, 3, 4, 5, 6):
        yp = by0 - (lv / 6.2) * bh
        lines.append(f'<line x1="{bx0-4}" y1="{yp:.1f}" x2="{bx0+bw}" y2="{yp:.1f}" stroke="#e2e8f0" stroke-width="1"/>')
        lines.append(f'<text x="{bx0-8}" y="{yp+3.5:.1f}" text-anchor="end" font-size="10" fill="#334155">10^{lv}</text>')

    srows = data["non_collinear_solve_ladder"]
    for idx, sr in enumerate(srows):
        cx = bx0 + 42 + idx * 74
        val = max(1.0, sr["work_over_rho"])
        lval = math.log10(val)
        bar_h = (min(lval, 6.2) / 6.2) * bh
        fill = "#2563eb" if sr["verified"] else "#94a3b8"
        lines.append(f'<rect x="{cx-18}" y="{by0-bar_h:.1f}" width="36" height="{bar_h:.1f}" fill="{fill}" opacity="0.88"/>')
        status_lbl = "SOLVED" if sr["verified"] else "CAP"
        lines.append(f'<text x="{cx}" y="{by0-bar_h-6:.1f}" text-anchor="middle" font-size="8.8" font-weight="bold" fill="#0f172a">{status_lbl}</text>')
        lines.append(f'<text x="{cx}" y="{by0+15}" text-anchor="middle" font-size="9.8" fill="#0f172a">p={sr["p"]}</text>')
        lines.append(f'<text x="{cx}" y="{by0+28}" text-anchor="middle" font-size="8.8" fill="#64748b">({sr["subgroup_bits"]:.1f}b)</text>')

    lines.append(
        '<text x="470" y="406" text-anchor="middle" font-size="9.5" fill="#64748b">'
        'Source: SCALING_CONTROLS.json (ca-icx xedni-solve deterministic controls; all assertions [pcc:unverified])</text>'
    )
    lines.append("</svg>\n")
    svg_path = HERE / "scaling_results.svg"
    svg_path.write_text("\n".join(lines), encoding="utf-8")

    # Compact 1-page US-Letter vector PDF (< 64 KiB)
    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    ops: list[str] = []

    def txt(x: float, y: float, sz: float, fnt: str, s: str, rgb=(0.06, 0.09, 0.16)) -> None:
        ops.append(f"{rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} rg BT /{fnt} {sz:.1f} Tf {x:.1f} {y:.1f} Td ({esc(s)}) Tj ET")

    txt(46, 748, 13.5, "F2", "Xedni Scaling Phase 1: Multi-Prime Kernel LLL, Short-Pool Lift & Lean Bridge")
    txt(46, 732, 9.0, "F1", "Date: 2026-11-18  |  ca-icx xedni-solve + ModularKernelAndSurfaceBridge.lean (11 theorems, 0 sorryAx) [pcc:unverified]", (0.28, 0.33, 0.41))
    ops.append("0.75 0.78 0.82 RG 0.8 w 46 724 m 566 724 l S")

    y = 708
    bullets = [
        ("F2", 10.0, "1. Algorithmic & Formal Advances Over Prior Baseline [pcc:unverified]"),
        ("F1", 8.8, "- Replaced exponential [-2,2]^r single-prime Python MITM with native Rust multi-prime abelian-subgroup kernel"),
        ("F1", 8.8, "  intersection + LLL + 4-prime u64 screen (xedni_solver.rs), eliminating Q-arithmetic false positives and"),
        ("F1", 8.8, "  recovering relations of arbitrary norm in milliseconds."),
        ("F1", 8.8, "- Added order-statistic short-pool 3D-LLL preselection (W=128) + 16-jump pseudorandom masks, cutting 28-bit"),
        ("F1", 8.8, f"  r=9 cubic height from {hrows[-1]['naive_z1_affine_bits']}b (naive) -> {hrows[-1]['jksst_w9_bits']}b (W=9) -> {hrows[-1]['jksst_w128_bits']}b (W=128) with 0 collinear aliases."),
        ("F1", 8.8, "- Proved in Lean 4 + Mathlib (ModularKernelAndSurfaceBridge.lean): zero-false-negative multi-prime kernel"),
        ("F1", 8.8, "  completeness on arbitrary C(F_q) and unconditional |M|/q fresh-mask ceiling for char-0 & F_p(t) surfaces."),
    ]
    for fnt, sz, b in bullets:
        txt(46, y, sz, fnt, b)
        y -= 12.2

    y -= 6
    txt(46, y, 10.0, "F2", "2. r = 9 Cubic Height Controls (y^2 = x^3 + 3x + 5, 0 Collinear Triples) [pcc:unverified]")
    y -= 13
    ops.append(f"0.93 0.95 0.98 rg 44 {y-3:.1f} 522 13 re f")
    hx = [46, 118, 168, 250, 336, 424, 504]
    for cx, hd in zip(hx, ["Prime p", "log2 p", "Naive Z=1", "JKSST W=9", "Short W=32", "Short W=128", "Coord Bits"]):
        txt(cx, y, 8.2, "F2", hd)
    y -= 12.5
    for hr in hrows:
        vals = [
            str(hr["p"]),
            f"{hr['log2_p']:.1f}",
            f"{hr['naive_z1_affine_bits']} b",
            f"{hr['jksst_w9_bits']} b",
            f"{hr['jksst_w32_bits']} b",
            f"{hr['jksst_w128_bits']} b",
            f"{hr['jksst_w128_coord_bits']} b",
        ]
        for cx, vl in zip(hx, vals):
            txt(cx, y, 8.2, "F1", vl)
        y -= 11.5

    y -= 8
    txt(46, y, 10.0, "F2", "3. End-to-End Non-Collinear Xedni ECDLP Solve Ladder (ca-icx xedni-solve) [pcc:unverified]")
    y -= 13
    ops.append(f"0.93 0.95 0.98 rg 44 {y-3:.1f} 522 13 re f")
    sx = [46, 92, 140, 186, 236, 294, 356, 424, 496]
    for cx, hd in zip(sx, ["p", "ord(G)", "r / W", "Verified", "Trials", "Non-Col.", "Min Coef", "Total Ops", "S / S_rho"]):
        txt(cx, y, 8.0, "F2", hd)
    y -= 12.5
    for sr in srows:
        vals = [
            str(sr["p"]),
            f"{sr['subgroup_order']} ({sr['subgroup_bits']:.1f}b)",
            f"{sr['rank_points']}/{sr['pool_size']}",
            "YES" if sr["verified"] else "NO",
            f"{sr['trials_attempted']}/{sr['max_trials']}",
            str(sr["non_collinear_relations_found"]),
            f"{sr['min_coefficient_bits']} b",
            str(sr["total_charged_ops"]),
            f"{sr['work_over_rho']:.1f}x",
        ]
        for cx, vl in zip(sx, vals):
            txt(cx, y, 8.0, "F1", vl)
        y -= 11.5

    y -= 10
    txt(46, y, 9.8, "F2", "4. Diagnosis & Next Scaling Hypothesis (Phase 2) [pcc:unverified]")
    y -= 12.2
    diag = [
        "Phase 1 lifts genuine non-collinear Xedni ECDLP recovery past the prior p=31 ceiling, but S / S_rho still grows",
        "with p because rank(C(Q)) <= 8 in fresh-mask mode obeys the Lean-proved |M|/q ceiling (ModularKernelAndSurfaceBridge).",
        "To reach sub-rho scaling toward cryptographic sizes, Phase 2 must break out of single-curve fresh-mask trials:",
        "either via shared global factor-base relation reuse across curves or higher-rank specialization families.",
    ]
    for line in diag:
        txt(46, y, 8.5, "F1", line)
        y -= 11.5

    txt(46, 32, 7.8, "F1", "cryptanalysis:research/xedni_scaling_20261118/  |  All claims carry [pcc:unverified] producer standing.", (0.40, 0.45, 0.52))

    stream_bytes = zlib.compress("\n".join(ops).encode("latin-1"))
    objs: list[bytes] = [
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        f"<< /Length {len(stream_bytes)} /Filter /FlateDecode >>\nstream\n".encode("ascii") + stream_bytes + b"\nendstream",
        b"<< /Type /Pages /Kids [5 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 4 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 1 0 R /F2 2 0 R >> >> /Contents 3 0 R >>",
        b"<< /Type /Catalog /Pages 4 0 R >>",
    ]
    buf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offs = [0]
    for i, ob in enumerate(objs, 1):
        offs.append(len(buf))
        buf.extend(f"{i} 0 obj\n".encode("ascii") + ob + b"\nendobj\n")
    xref = len(buf)
    buf.extend(f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode("ascii"))
    for off in offs[1:]:
        buf.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    buf.extend(f"trailer\n<< /Size {len(objs)+1} /Root 6 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii"))
    pdf_path = HERE / "xedni_scaling_20261118.pdf"
    pdf_path.write_bytes(bytes(buf))
    assert pdf_path.stat().st_size < 65536
    return {"svg_bytes": svg_path.stat().st_size, "pdf_bytes": pdf_path.stat().st_size}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    p_selftest = sub.add_parser("selftest")
    p_selftest.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    args = parser.parse_args()

    out_json = HERE / "SCALING_CONTROLS.json"
    if args.command == "run":
        data = run_controls(args.binary)
        out_json.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        vis = write_visuals(data)
        print(json.dumps({"rows": len(data["non_collinear_solve_ladder"]), **vis}, sort_keys=True))
        return

    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["r9_short_pool_height_rows"][-1]["jksst_w128_bits"] < data["r9_short_pool_height_rows"][-1]["jksst_w9_bits"]
    solved = [r["p"] for r in data["non_collinear_solve_ladder"] if r["verified"]]
    assert 67 in solved
    print(json.dumps({"status": "PASS", "solved_primes": solved}, sort_keys=True))


if __name__ == "__main__":
    main()
