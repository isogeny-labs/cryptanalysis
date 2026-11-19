#!/usr/bin/env python3
"""Paired JKSST projective-frame vs naive plane-cubic runner with collinearity separation.

`selftest` runs deterministic fixed controls only (no natural-lift trials).
`run` enforces `scripts/checkpoint.sh gate` before generating the first natural
row, in strict compliance with repository experiment governance.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_nov17_panel import is_collinear_alias as _is_collinear_alias  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
NOV17_SWEEP = ROOT / "research/xedni_plane_group_20261117/sweep.py"
SPEC = importlib.util.spec_from_file_location("xedni_plane_group_20261117", NOV17_SWEEP)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {NOV17_SWEEP}")
nov17 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(nov17)


def is_collinear_alias(
    relation: tuple[int, ...], u: int, v: int, points: list[tuple[int, int, int]]
) -> bool:
    return _is_collinear_alias(relation, (u, v), points)


def find_noncollinear_target_first_relation(
    points: list[tuple[int, int, int]],
    coefficients: tuple[int, ...],
    origin: tuple[int, int, int],
    u: int,
    v: int,
    discriminant: int,
    bound: int,
    subgroup_order: int,
) -> dict:
    q = next(q for q in nov17.Q_PRIMES if discriminant % q)
    cq = tuple(c % q for c in coefficients)
    oq = nov17.primitive(origin, q)
    pq = [nov17.primitive(pt, q) for pt in points]
    tables = [
        {scalar: nov17.group_mul(cq, oq, scalar, pt, q) for scalar in range(-bound, bound + 1)}
        for pt in pq
    ]
    half = (len(points) + 1) // 2

    def enum_sums(indices):
        rows = [((), oq)]
        for idx in indices:
            rows = [
                (rel + (sc,), nov17.group_add(cq, oq, tot, tables[idx][sc], q))
                for rel, tot in rows
                for sc in range(-bound, bound + 1)
            ]
        return rows

    left: dict[tuple[int, int, int], list[tuple[int, ...]]] = {}
    for rel, tot in enum_sums(range(half)):
        left.setdefault(tot, []).append(rel)
    candidates: list[tuple[int, ...]] = []
    for rel, tot in enum_sums(range(half, len(points))):
        opp = nov17.group_neg(cq, oq, tot, q)
        for pref in left.get(opp, ()):
            cand = pref + rel
            if any(cand):
                candidates.append(cand)

    # Order: (1) non-collinear before collinear, (2) invertible target coeff before zero, (3) L1 norm
    def sort_key(cand: tuple[int, ...]):
        col = 1 if is_collinear_alias(cand, u, v, points) else 0
        inv_t = 0 if math.gcd(cand[-1] % subgroup_order, subgroup_order) == 1 else 1
        return (col, inv_t, sum(abs(x) for x in cand), cand)

    candidates.sort(key=sort_key)
    exact_checks = 0
    for cand in candidates:
        exact_checks += 1
        if nov17.relation_sum(coefficients, origin, cand, points) == origin:
            return {
                "found": list(cand),
                "is_collinear_alias": is_collinear_alias(cand, u, v, points),
                "modular_candidates": len(candidates),
                "exact_checks": exact_checks,
            }
    return {
        "found": None,
        "is_collinear_alias": False,
        "modular_candidates": len(candidates),
        "exact_checks": exact_checks,
    }


def selftest() -> dict:
    # Planted rank-9 cubic y^2 = x^3 - x + 1 with an injected irrelevant known-only collinearity:
    # verify that non-collinear target-bearing exact relation (0,0,2,0,0,0,0,0,-1) is prioritized
    # and recovers target scalar 9, while a collinearity is classified as an alias.
    coeffs = (1, 0, 0, 0, 0, 0, -1, -1, 0, 1)
    raw_points = (
        ("0", "1", "1"),
        ("2", "-7", "8"),
        ("56", "419", "1"),
        ("-6244", "24655", "21952"),
        ("5232472", "-8824453", "11089567"),
        ("8246188998", "30795303833", "588480472"),
        ("-51055373209680", "101098481076377", "85923747076383"),
        ("1796402375990961480", "-2098030206970736191", "2631958890650432000"),
        ("160221897655974195623120", "396235626125845757178647", "25634128246348207648607"),
    )
    pts = [nov17.primitive(map(int, p)) for p in raw_points]
    origin, u, v = nov17.choose_chord_origin(coeffs, pts, 8)
    res = find_noncollinear_target_first_relation(pts, coeffs, origin, u, v, 635904, 2, 73)
    assert res["found"] is not None
    assert res["is_collinear_alias"] is False
    rel = tuple(res["found"])
    # Independently re-verify exact projective sum over Q:
    assert nov17.relation_sum(coeffs, origin, rel, pts) == origin
    residue, recovered = nov17.source_recovery(rel, list(range(1, 10)), -3, 73)
    assert residue == 0 and recovered == 9

    # Collinear alias detection check:
    col_pts = [(0, 1, 1), (2, 5, 1), (4, 9, 1), (1, 0, 1)]
    assert is_collinear_alias((0, 0, 1, -1), 0, 1, col_pts) is False
    # Fixed vector e_0 + e_1 + e_2 corresponds to local (0, 0, 1, 0) when origin_pair=(0,1), S=1:
    # transport: [0+1, 0+1, 1, 0] = [1, 1, 1, 0] -> collinear!
    assert is_collinear_alias((0, 0, 1, 0), 0, 1, col_pts) is True
    return {
        "status": "PASS",
        "selected_relation": res["found"],
        "is_collinear_alias": res["is_collinear_alias"],
        "recovered_target": recovered,
    }


def enforce_checkpoint_gate() -> None:
    gate = subprocess.run(
        ["bash", str(ROOT / "scripts/checkpoint.sh"), "gate"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if gate.returncode != 0:
        msg = (gate.stderr or gate.stdout).strip()
        raise SystemExit(
            f"refusing to generate natural-lift rows before checkpoint gate passes:\n{msg}"
        )


def run_paired_trial(
    binary: Path, tempdir: str, p: int, family: str, r: int, idx: int, master: str, pools: dict
) -> dict:
    rng = random.Random(f"{master}|{p}|{family}|{r}|{idx}")
    curves, sq = pools[(p, family)]
    a, b, cardinality = curves[idx % len(curves)]
    row: dict = {
        "p": p,
        "family": family,
        "r": r,
        "idx": idx,
        "a": a,
        "b": b,
        "curve_order": cardinality,
        "status": "",
    }
    for _ in range(200):
        x = rng.randrange(p)
        ordinates = sq.get((x**3 + a * x + b) % p)
        if ordinates:
            break
    else:
        row["status"] = "no_point"
        return row
    base = (x, rng.choice(ordinates))
    order = nov17.old.divisors_order(cardinality, base, a, p)
    row["subgroup_order"] = order
    if order < 2 * r + 1:
        row["status"] = "small_order"
        return row
    classes, multipliers = set(), []
    while len(multipliers) < r - 1:
        m = rng.randrange(1, order)
        if m in classes or order - m in classes:
            continue
        classes.add(m)
        multipliers.append(m)
    while True:
        target = rng.randrange(1, order)
        if target not in classes and order - target not in classes:
            break
    multipliers.append(target)
    finite_points = [nov17.old.ec_mul_p(m, base, a, p) for m in multipliers]
    if any(pt is None for pt in finite_points):
        row["status"] = "identity"
        return row

    source_cubic = [1, 0, 0, 0, 0, 0, -1, a, 0, b]
    input_path = Path(tempdir) / f"jksst-{os.getpid()}.json"
    input_path.write_text(
        json.dumps(
            {
                "modulus": str(p),
                "source_coefficients": [str(c) for c in source_cubic],
                "source_points": [[str(px), str(py), "1"] for px, py in finite_points],
                "point_lift_mode": "projective-lll",
                "max_frames": 126,
                "reject_collinear_lifts": False,
            }
        ),
        encoding="utf-8",
    )
    cp = subprocess.run(
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
            str(max(1, 3 ** (10 - r))),
        ],
        capture_output=True,
        text=True,
    )
    if cp.returncode != 0:
        row["status"] = "jksst_lift_error"
        row["error"] = (cp.stderr or cp.stdout)[-300:]
        return row
    res = json.loads(cp.stdout)["result"]
    coeffs = tuple(int(v) for v in res["optimized_coefficients"])
    pts = [nov17.primitive(map(int, pt)) for pt in res["lifted_points"]]
    disc = int(res["optimized_score"]["discriminant"])
    row["jksst_coef_bits"] = res["optimized_score"]["coefficient_height_bits"]
    row["jksst_disc_bits"] = res["optimized_score"]["discriminant_bits"]
    row["pre_lift_collinear_count"] = len(res["pre_lift_collinear_triples"])

    origin, u, v = nov17.choose_chord_origin(coeffs, pts, r - 1)
    origin_mult = -(multipliers[u] + multipliers[v])
    search = find_noncollinear_target_first_relation(
        pts, coeffs, origin, u, v, disc, nov17.NBOX, order
    )
    row["status"] = "ok"
    row["modular_candidates"] = search["modular_candidates"]
    row["exact_checks"] = search["exact_checks"]
    if search["found"] is None:
        row["certified"] = 0
        row["cubic_dependent_success"] = 0
        row["dl_recovered"] = 0
        return row

    rel = tuple(search["found"])
    exact_sum = nov17.relation_sum(coeffs, origin, rel, pts)
    residue, recovered = nov17.source_recovery(rel, multipliers, origin_mult, order)
    if exact_sum != origin or residue != 0:
        row["status"] = "relation_cert_failed"
        return row
    row["certified"] = 1
    row["is_collinear_alias"] = int(search["is_collinear_alias"])
    row["cubic_dependent_success"] = int(not search["is_collinear_alias"])
    row["relation"] = list(rel)
    row["dl_recovered"] = int(recovered == target % order)
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("selftest")
    run_p = sub.add_parser("run")
    run_p.add_argument("--binary", type=Path, required=True)
    run_p.add_argument("--output", type=Path, required=True)
    run_p.add_argument("--master", default="xedni-jksst-noncollinear-20261118-v1")
    run_p.add_argument("--primes", default="31,67,127,251,509")
    run_p.add_argument("--families", default="generic,j0")
    run_p.add_argument("--r-values", default="6,7,8,9")
    run_p.add_argument("--trials", type=int, default=25)
    args = parser.parse_args()

    if args.command == "selftest":
        print(json.dumps(selftest(), sort_keys=True))
        return

    enforce_checkpoint_gate()
    primes = tuple(map(int, args.primes.split(",")))
    families = tuple(args.families.split(","))
    r_values = tuple(map(int, args.r_values.split(",")))
    pools = {
        (p, fam): nov17.old.curve_pool(p, fam, random.Random(f"{args.master}|pool|{p}|{fam}"))
        for p in primes
        for fam in families
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    jobs = [
        (p, fam, r, idx)
        for p in primes
        for fam in families
        for r in r_values
        for idx in range(args.trials)
    ]
    with tempfile.TemporaryDirectory(prefix="xedni-jksst-") as tmp, args.output.open(
        "w", encoding="utf-8"
    ) as out:
        for p, fam, r, idx in jobs:
            row = run_paired_trial(args.binary, tmp, p, fam, r, idx, args.master, pools)
            out.write(json.dumps(row, sort_keys=True) + "\n")
            out.flush()
    print(json.dumps({"rows": len(jobs), "seconds": time.time() - t0}, sort_keys=True))


if __name__ == "__main__":
    main()
