#!/usr/bin/env python3
"""Deterministic fixed-instance controls for JKSST projective-frame + 3D-LLL lifting.

Compares five deterministic plane-cubic lifting arms on identical fixed point
configurations across primes p in {67, 251, 4091, 65519, 1048571, 268435399}
(all p = 3 mod 4) at r = 9, and cross-checks the Rust `ca-icx` binary's
`--model jksst-plane-cubic` against an independent Python implementation.

No natural-lift random-target experiment sweep is executed here; these are
fixed deterministic representation/height controls and planted-curve
certificates.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_nov17_panel import det_bareiss, old as old_sweep  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BINARY = ROOT / "suite/target/release/ca-icx"
XEDNI_LIFT_RS = ROOT / "suite/src/cryptanalysis/xedni_lift.rs"
CONTROL_PRIMES = (67, 251, 4091, 65519, 1048571, 268435399)


def deterministic_points_on_curve(p: int, a: int, b: int, count: int) -> list[tuple[int, int, int]]:
    assert p % 4 == 3
    exp = (p + 1) // 4
    pts: list[tuple[int, int, int]] = []
    seen_x: set[int] = set()
    step = (p * 37) // 100 + 1
    while math.gcd(step, p) != 1:
        step += 1
    x = (p * 19) // 100 + 1
    while len(pts) < count:
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


def balanced(val: int, p: int) -> int:
    r = val % p
    return r - p if r > p // 2 else r


def incidence(pt: tuple[int, int, int]) -> list[int]:
    x, y, z = pt
    return [x**3, x * x * y, x * y * y, y**3, x * x * z, x * y * z, y * y * z, x * z * z, y * z * z, z**3]


def prim_kernel_9x10(pts: list[tuple[int, int, int]]) -> list[int]:
    rows = [incidence(pt) for pt in pts]
    vec = []
    for col in range(10):
        sub = [[row[j] for j in range(10) if j != col] for row in rows]
        d = det_bareiss(sub)
        vec.append(-d if (col % 2 == 1) else d)
    g = 0
    for v in vec:
        g = math.gcd(g, abs(v))
    if g == 0:
        return [0] * 10
    vec = [v // g for v in vec]
    first = next(v for v in vec if v != 0)
    if first < 0:
        vec = [-v for v in vec]
    return vec


def lll_3d_python(basis_in: list[list[int]]) -> list[list[int]]:
    b = [row[:] for row in basis_in]
    while True:
        gs = []
        mu = [[Fraction(0)] * 3 for _ in range(3)]
        bnorm = [Fraction(0)] * 3
        for i in range(3):
            vi = [Fraction(x) for x in b[i]]
            for j in range(i):
                mu[i][j] = sum(Fraction(b[i][t]) * gs[j][t] for t in range(3)) / bnorm[j]
                vi = [vi[t] - mu[i][j] * gs[j][t] for t in range(3)]
            gs.append(vi)
            bnorm[i] = sum(x * x for x in vi)
        for i in range(1, 3):
            for j in range(i - 1, -1, -1):
                q = round(mu[i][j])
                if q != 0:
                    b[i] = [b[i][t] - q * b[j][t] for t in range(3)]
                    for k in range(j):
                        mu[i][k] -= q * mu[j][k]
                    mu[i][j] -= q
        swapped = False
        for k in range(1, 3):
            if bnorm[k] < (Fraction(99, 100) - mu[k][k - 1] ** 2) * bnorm[k - 1]:
                b[k], b[k - 1] = b[k - 1], b[k]
                swapped = True
                break
        if not swapped:
            return b


def short_proj_lift_python(pt_mod_p: tuple[int, int, int], p: int) -> tuple[int, int, int]:
    idx = next(i for i in range(3) if pt_mod_p[i] % p != 0)
    inv = pow(pt_mod_p[idx] % p, -1, p)
    canon = tuple((x * inv) % p for x in pt_mod_p)
    basis = [[balanced(canon[0], p), balanced(canon[1], p), balanced(canon[2], p)]]
    for j in range(3):
        if j != idx:
            row = [0, 0, 0]
            row[j] = p
            basis.append(row)
    red = lll_3d_python(basis)
    best = None
    for c0, c1, c2 in itertools.product((-1, 0, 1), repeat=3):
        if (c0, c1, c2) == (0, 0, 0):
            continue
        cand = [c0 * red[0][k] + c1 * red[1][k] + c2 * red[2][k] for k in range(3)]
        if all(x % p == 0 for x in cand):
            continue
        g = math.gcd(math.gcd(abs(cand[0]), abs(cand[1])), abs(cand[2]))
        cand = [x // g for x in cand]
        if next(x for x in cand if x != 0) < 0:
            cand = [-x for x in cand]
        key = (sum(x * x for x in cand), tuple(cand))
        if best is None or key < best:
            best = key
    assert best is not None
    return best[1]


def run_ca_icx_jksst(
    binary: Path,
    p: int,
    source_cubic: list[int],
    pts: list[tuple[int, int, int]],
    point_lift_mode: str,
    max_frames: int,
    frame_indices: list[int] | None = None,
) -> dict:
    payload: dict = {
        "modulus": str(p),
        "source_coefficients": [str(c) for c in source_cubic],
        "source_points": [[str(x) for x in pt] for pt in pts],
        "point_lift_mode": point_lift_mode,
        "max_frames": max_frames,
        "reject_collinear_lifts": False,
    }
    if frame_indices is not None:
        payload["frame_indices"] = frame_indices
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(payload, handle)
        input_path = Path(handle.name)
    try:
        completed = subprocess.run(
            [
                str(binary),
                "--json",
                "xedni-lift",
                "--model",
                "jksst-plane-cubic",
                "--input",
                str(input_path),
                "--radius",
                "1",
                "--max-candidates",
                "64",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(completed.stdout)["result"]
    finally:
        input_path.unlink(missing_ok=True)


def run_ca_icx_naive_affine(
    binary: Path, p: int, source_cubic: list[int], pts: list[tuple[int, int, int]]
) -> dict:
    bal_pts = [(balanced(x, p), balanced(y, p), 1) for x, y, _ in pts]
    matrix = [incidence(pt) for pt in bal_pts]
    values = [sum(a * b for a, b in zip(row, source_cubic)) for row in matrix]
    sol = old_sweep.solve_affine(matrix, [-v // p for v in values], 10)
    assert sol is not None
    delta, kernel, rank = sol
    assert rank == len(pts)
    particular = [source_cubic[i] + p * delta[i] for i in range(10)]
    directions = [[p * v for v in vec] for vec in kernel]
    payload = {
        "particular": [str(v) for v in particular],
        "directions": [[str(v) for v in vec] for vec in directions],
        "projective_points": [[str(v) for v in pt] for pt in bal_pts],
        "congruence_modulus": str(p),
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(payload, handle)
        input_path = Path(handle.name)
    try:
        completed = subprocess.run(
            [
                str(binary),
                "--json",
                "xedni-lift",
                "--model",
                "plane-cubic",
                "--input",
                str(input_path),
                "--radius",
                "1",
                "--max-candidates",
                str(max(1, 3 ** len(directions))),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(completed.stdout)["result"]
    finally:
        input_path.unlink(missing_ok=True)


def planted_unimodular_frame_recovery_control() -> dict:
    """Verify PGL_3 frame transformation + chord-origin recovery on a planted rank-9 Q-cubic."""
    sweep_spec = importlib.util.spec_from_file_location(
        "nov17_sweep", ROOT / "research/xedni_plane_group_20261117/sweep.py"
    )
    assert sweep_spec and sweep_spec.loader
    sw = importlib.util.module_from_spec(sweep_spec)
    sweep_spec.loader.exec_module(sw)

    # Apply an invertible unimodular matrix U in GL_3(Z) to y^2 = x^3 - x + 1,
    # creating a general 10-coefficient cubic over Q with NO Weierstrass flex at (0:1:0).
    u_mat = ((1, 2, 1), (0, 1, 1), (1, 1, 2))  # det = 1*(2-1) - 2*(0-1) + 1*(0-1) = 2 != 0
    u_inv_num = (
        (1, -3, 1),
        (1, 1, -1),
        (-1, 1, 1),
    )  # U * U_adj = 2 * I_3

    base_coeffs = (1, 0, 0, 0, 0, 0, -1, -1, 0, 1)
    raw_points = (
        (0, 1, 1),
        (2, -7, 8),
        (56, 419, 1),
        (-6244, 24655, 21952),
        (5232472, -8824453, 11089567),
        (8246188998, 30795303833, 588480472),
        (-51055373209680, 101098481076377, 85923747076383),
        (1796402375990961480, -2098030206970736191, 2631958890650432000),
        (160221897655974195623120, 396235626125845757178647, 25634128246348207648607),
    )
    transformed_pts = [
        sw.primitive(tuple(sum(u_mat[r][c] * pt[c] for c in range(3)) for r in range(3)))
        for pt in raw_points
    ]
    # Unique primitive integer cubic through the 9 transformed points:
    framed_coeffs = tuple(prim_kernel_9x10(transformed_pts))
    assert all(sw.on_cubic(framed_coeffs, pt) for pt in transformed_pts)
    origin, left_idx, right_idx = sw.choose_chord_origin(framed_coeffs, transformed_pts, 8)
    assert (left_idx, right_idx) == (0, 1)
    relation = (0, 0, 2, 0, 0, 0, 0, 0, -1)
    assert sw.relation_sum(framed_coeffs, origin, relation, transformed_pts) == origin
    residue, recovered = sw.source_recovery(relation, list(range(1, 10)), -3, 73)
    assert residue == 0 and recovered == 9
    # Verify U_adj maps origin back to the original chord origin in P^2(Q):
    orig_pts = [sw.primitive(pt) for pt in raw_points]
    orig_origin, _, _ = sw.choose_chord_origin(base_coeffs, orig_pts, 8)
    mapped_back = sw.primitive(tuple(sum(u_inv_num[r][c] * origin[c] for c in range(3)) for r in range(3)))
    assert mapped_back == orig_origin
    return {
        "status": "PASS",
        "framed_coefficients": list(framed_coeffs),
        "recovered_target_scalar": recovered,
        "chord_origin_equivariant_over_q": True,
    }


def build_control_report(binary: Path) -> dict:
    rust_source_sha = hashlib.sha256(XEDNI_LIFT_RS.read_bytes()).hexdigest()
    source_cubic = [1, 0, 0, 0, 0, 0, -1, 3, 0, 5]
    rows = []

    for p in CONTROL_PRIMES:
        pts = deterministic_points_on_curve(p, 3, 5, 9)
        log2_p = math.log2(p)

        naive_aff = run_ca_icx_naive_affine(binary, p, source_cubic, pts)
        naive_hom_vec = prim_kernel_9x10([(balanced(x, p), balanced(y, p), 1) for x, y, _ in pts])
        naive_hom_coef_bits = max(abs(x).bit_length() for x in naive_hom_vec)

        jksst_f1_aff = run_ca_icx_jksst(binary, p, source_cubic, pts, "affine-balanced", 1)
        jksst_f1_lll = run_ca_icx_jksst(binary, p, source_cubic, pts, "projective-lll", 1)
        jksst_f126_lll = run_ca_icx_jksst(binary, p, source_cubic, pts, "projective-lll", 126)

        # Cross-check ca-icx winning frame's lifted points and cubic against independent Python!
        win_frame = jksst_f126_lll["frame_indices"]
        rust_pts = [tuple(int(v) for v in pt) for pt in jksst_f126_lll["lifted_points"]]
        m_from = [[int(v) for v in r_] for r_ in jksst_f126_lll["matrix_from_source_mod_p"]]
        for idx, pt in enumerate(pts):
            if idx in win_frame:
                continue
            mapped = tuple(sum(m_from[r_][c_] * pt[c_] for c_ in range(3)) % p for r_ in range(3))
            py_pt = short_proj_lift_python(mapped, p)
            if py_pt != rust_pts[idx]:
                raise ValueError(f"Python/Rust 3D-LLL mismatch at p={p}, idx={idx}: {py_pt} vs {rust_pts[idx]}")
        py_cubic = prim_kernel_9x10(rust_pts)
        rust_cubic = [int(v) for v in jksst_f126_lll["optimized_coefficients"]]
        if py_cubic != rust_cubic:
            raise ValueError(f"Python/Rust primitive r=9 cubic mismatch at p={p}")

        aff_cb = naive_aff["optimized_score"]["coefficient_height_bits"]
        aff_db = naive_aff["optimized_score"]["discriminant_bits"]
        f1a_cb = jksst_f1_aff["optimized_score"]["coefficient_height_bits"]
        f1a_db = jksst_f1_aff["optimized_score"]["discriminant_bits"]
        f1l_cb = jksst_f1_lll["optimized_score"]["coefficient_height_bits"]
        f1l_db = jksst_f1_lll["optimized_score"]["discriminant_bits"]
        f126_cb = jksst_f126_lll["optimized_score"]["coefficient_height_bits"]
        f126_db = jksst_f126_lll["optimized_score"]["discriminant_bits"]

        rows.append(
            {
                "p": p,
                "log2_p": round(log2_p, 4),
                "r": 9,
                "naive_affine_congruence": {
                    "coefficient_bits": aff_cb,
                    "discriminant_bits": aff_db,
                    "coef_bits_per_log2_p": round(aff_cb / log2_p, 4),
                },
                "naive_homogeneous_congruence": {
                    "coefficient_bits": naive_hom_coef_bits,
                    "coef_bits_per_log2_p": round(naive_hom_coef_bits / log2_p, 4),
                },
                "jksst_1frame_affine_points": {
                    "coefficient_bits": f1a_cb,
                    "discriminant_bits": f1a_db,
                    "coef_bits_per_log2_p": round(f1a_cb / log2_p, 4),
                },
                "jksst_1frame_projective_lll": {
                    "coefficient_bits": f1l_cb,
                    "discriminant_bits": f1l_db,
                    "max_point_coord_bits": jksst_f1_lll["max_point_coordinate_bits"],
                    "coef_bits_per_log2_p": round(f1l_cb / log2_p, 4),
                },
                "jksst_126frames_projective_lll": {
                    "coefficient_bits": f126_cb,
                    "discriminant_bits": f126_db,
                    "max_point_coord_bits": jksst_f126_lll["max_point_coordinate_bits"],
                    "winning_frame": win_frame,
                    "pre_lift_collinear_triples": jksst_f126_lll["pre_lift_collinear_triples"],
                    "coef_bits_per_log2_p": round(f126_cb / log2_p, 4),
                    "coef_bit_reduction_ratio_vs_naive_affine": round(aff_cb / f126_cb, 4),
                    "disc_bit_reduction_ratio_vs_naive_affine": round(aff_db / f126_db, 4),
                },
                "python_rust_parity": True,
            }
        )

    planted = planted_unimodular_frame_recovery_control()
    return {
        "schema": "cryptanalysis.xedni-jksst-frame-height-control/v1",
        "rust_source_path": str(XEDNI_LIFT_RS.relative_to(ROOT)),
        "rust_source_sha256": rust_source_sha,
        "curve_equation_mod_p": "y^2 = x^3 + 3x + 5",
        "scope": "deterministic fixed-instance representation and height-scaling controls; not a natural-lift relation-yield or timing benchmark",
        "r9_scaling_rows": rows,
        "planted_gl3_frame_recovery_control": planted,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    selftest_p = sub.add_parser("selftest")
    selftest_p.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    run_p = sub.add_parser("run")
    run_p.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    run_p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "selftest":
        report = build_control_report(args.binary)
        planted = report["planted_gl3_frame_recovery_control"]
        last = report["r9_scaling_rows"][-1]
        assert last["p"] == 268435399
        assert last["jksst_126frames_projective_lll"]["coefficient_bits"] * 2 < (
            last["naive_affine_congruence"]["coefficient_bits"]
        )
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "planted_recovered": planted["recovered_target_scalar"],
                    "p28_naive_coef_bits": last["naive_affine_congruence"]["coefficient_bits"],
                    "p28_jksst126_coef_bits": last["jksst_126frames_projective_lll"][
                        "coefficient_bits"
                    ],
                },
                sort_keys=True,
            )
        )
        return

    report = build_control_report(args.binary)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for row in report["r9_scaling_rows"]:
        na = row["naive_affine_congruence"]
        jk = row["jksst_126frames_projective_lll"]
        print(
            f"p={row['p']:10d} ({row['log2_p']:5.1f}b): "
            f"naive_aff={na['coefficient_bits']:4d}b (disc {na['discriminant_bits']:4d}b) -> "
            f"jksst126={jk['coefficient_bits']:4d}b (disc {jk['discriminant_bits']:4d}b) "
            f"[{jk['coef_bit_reduction_ratio_vs_naive_affine']:.2f}x smaller]"
        )


if __name__ == "__main__":
    main()
