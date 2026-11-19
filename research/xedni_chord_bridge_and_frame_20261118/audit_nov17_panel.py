#!/usr/bin/env python3
"""Forensic algebraic-geometric decomposition of the frozen Nov 17 r=6..9 Xedni panel.

Reads the immutable `research/xedni_plane_group_20261117/run/rows.jsonl` without
modifying any historical file or generating new natural-lift trials.
Verifies the frozen SHA-256 digest, replays the exact deterministic pre-lift
point construction for all 1,205 eligible rows, transports every certified
origin-local relation `n` to canonical flex-divisor coordinates
`r = n + S * e_u + S * e_v` (`S = sum(n)`), and classifies each relation into:
  1. pre-lift integer-plane collinearity (`det([P_a, P_b, P_c]) = 0` over Z),
  2. irreducible six-point integer conic (`det_6x6 = 0`), or
  3. genuine cubic-dependent Mordell--Weil relation.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import random
import statistics


ROOT = Path(__file__).resolve().parents[2]
ROWS_PATH = ROOT / "research/xedni_plane_group_20261117/run/rows.jsonl"
EXPECTED_ROWS_SHA256 = "2226d6fdfb56f87022eac8ed5ee7f38ad1e115375aaa057d69dfe67c40f3f773"
MASTER_SEED = "xedni-plane-r6789-20261117-v1"

OLD_SWEEP = ROOT / "research/xedni_lift_success_20261112/sweep.py"
SPEC = importlib.util.spec_from_file_location("xedni_lift_success_20261112", OLD_SWEEP)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {OLD_SWEEP}")
old = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(old)


def det3(p1: tuple[int, int, int], p2: tuple[int, int, int], p3: tuple[int, int, int]) -> int:
    return (
        p1[0] * (p2[1] * p3[2] - p2[2] * p3[1])
        - p1[1] * (p2[0] * p3[2] - p2[2] * p3[0])
        + p1[2] * (p2[0] * p3[1] - p2[1] * p3[0])
    )


def det_bareiss(matrix: list[list[int]]) -> int:
    n = len(matrix)
    a = [row[:] for row in matrix]
    sign = 1
    prev = 1
    for k in range(n - 1):
        piv = next((i for i in range(k, n) if a[i][k] != 0), None)
        if piv is None:
            return 0
        if piv != k:
            a[k], a[piv] = a[piv], a[k]
            sign = -sign
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                a[i][j] = (a[i][j] * a[k][k] - a[i][k] * a[k][j]) // prev
            a[i][k] = 0
        prev = a[k][k]
    return sign * a[n - 1][n - 1]


def transport_to_fixed_flex(local_relation: list[int] | tuple[int, ...], origin_pair: list[int] | tuple[int, int]) -> list[int]:
    s = sum(local_relation)
    fixed = list(local_relation)
    fixed[origin_pair[0]] += s
    fixed[origin_pair[1]] += s
    return fixed


def is_collinear_alias(
    local_relation: list[int] | tuple[int, ...],
    origin_pair: list[int] | tuple[int, int],
    points: list[tuple[int, int, int]],
) -> bool:
    fixed = transport_to_fixed_flex(local_relation, origin_pair)
    supp = [i for i, val in enumerate(fixed) if val != 0]
    return (
        len(supp) == 3
        and {abs(fixed[i]) for i in supp} == {1}
        and fixed[supp[0]] == fixed[supp[1]] == fixed[supp[2]]
        and det3(points[supp[0]], points[supp[1]], points[supp[2]]) == 0
    )


def reconstruct_trial_points(
    row: dict, pools: dict[tuple[int, str], tuple[list[tuple[int, int, int]], dict[int, list[int]]]]
) -> tuple[list[tuple[int, int, int]], list[int]]:
    p = row["p"]
    family = row["family"]
    lift = row["lift"]
    r = row["r"]
    index = row["idx"]
    rng = random.Random(f"{MASTER_SEED}|{p}|{family}|{lift}|{r}|{index}")
    curves, sq = pools[(p, family)]
    a, b, cardinality = curves[index % len(curves)]
    if (a, b, cardinality) != (row["a"], row["b"], row["curve_order"]):
        raise ValueError(f"curve mismatch on row {row}")
    for _ in range(200):
        x = rng.randrange(p)
        ordinates = sq.get((x**3 + a * x + b) % p)
        if ordinates:
            break
    else:
        raise ValueError("unexpected no_point on ok row")
    base = (x, rng.choice(ordinates))
    order = old.divisors_order(cardinality, base, a, p)
    if order != row["subgroup_order"]:
        raise ValueError(f"subgroup order mismatch on row {row}")
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
    finite_points = [old.ec_mul_p(m, base, a, p) for m in multipliers]
    points = []
    for px, py in finite_points:
        bx = px - p if px > p // 2 else px
        by = py - p if py > p // 2 else py
        if lift == "wide":
            bx += p * rng.choice((-1, 0, 1))
            by += p * rng.choice((-1, 0, 1))
        points.append((bx, by, 1))
    return points, multipliers


def analyze_panel(rows_path: Path = ROWS_PATH) -> dict:
    raw_bytes = rows_path.read_bytes()
    actual_sha = hashlib.sha256(raw_bytes).hexdigest()
    if actual_sha != EXPECTED_ROWS_SHA256:
        raise ValueError(f"rows.jsonl SHA-256 mismatch: {actual_sha}")
    rows = [json.loads(line) for line in raw_bytes.decode("utf-8").splitlines() if line.strip()]
    if len(rows) != 1600:
        raise ValueError(f"expected 1600 rows, got {len(rows)}")

    pools = {
        (p, fam): old.curve_pool(p, fam, random.Random(f"{MASTER_SEED}|pool|{p}|{fam}"))
        for p in (31, 67, 127, 251)
        for fam in ("generic", "j0")
    }

    ok_rows = 0
    certified_total = 0
    collinear_certified = 0
    cubic_dependent_certified = 0
    rows_with_any_collinear = 0
    rows_with_multi_collinear = 0
    rows_with_target_collinear = 0
    missed_collinear_rows = 0
    irreducible_conic_rows = 0

    by_r: dict[str, dict[str, int]] = {
        str(r): {
            "eligible": 0,
            "certified": 0,
            "collinear_certified": 0,
            "cubic_dependent_certified": 0,
            "recovered_selected": 0,
            "rows_with_target_collinear": 0,
            "point_triples_per_trial": math.comb(r, 3),
        }
        for r in (6, 7, 8, 9)
    }
    by_prime: dict[str, dict[str, int]] = {
        str(p): {
            "eligible": 0,
            "certified": 0,
            "collinear_certified": 0,
            "cubic_dependent_certified": 0,
        }
        for p in (31, 67, 127, 251)
    }
    by_lift: dict[str, dict[str, int]] = {
        lift: {"eligible": 0, "certified": 0, "collinear_certified": 0, "cubic_dependent_certified": 0}
        for lift in ("balanced", "wide")
    }
    height_scaling: dict[str, dict[str, float]] = {}
    height_buckets: dict[tuple[int, int, str], list[tuple[int, int]]] = collections.defaultdict(list)
    cubic_dependent_examples = []

    for row in rows:
        if row["status"] != "ok":
            continue
        ok_rows += 1
        r_key = str(row["r"])
        p_key = str(row["p"])
        lift_key = row["lift"]
        by_r[r_key]["eligible"] += 1
        by_prime[p_key]["eligible"] += 1
        by_lift[lift_key]["eligible"] += 1
        height_buckets[(row["r"], row["p"], row["lift"])].append(
            (row["coefficient_bits"], row["discriminant_bits"])
        )

        points, multipliers = reconstruct_trial_points(row, pools)
        r = row["r"]
        triples = [
            (i, j, k)
            for i, j, k in itertools.combinations(range(r), 3)
            if det3(points[i], points[j], points[k]) == 0
        ]
        if triples:
            rows_with_any_collinear += 1
            if len(triples) > 1:
                rows_with_multi_collinear += 1
            if any((r - 1) in t for t in triples):
                rows_with_target_collinear += 1
                by_r[r_key]["rows_with_target_collinear"] += 1
            if row["success"] == 0:
                missed_collinear_rows += 1

        has_conic = False
        for sext in itertools.combinations(range(r), 6):
            mat = [
                [
                    1,
                    points[i][0],
                    points[i][1],
                    points[i][0] ** 2,
                    points[i][0] * points[i][1],
                    points[i][1] ** 2,
                ]
                for i in sext
            ]
            if det_bareiss(mat) == 0:
                if not any(
                    det3(points[a_], points[b_], points[c_]) == 0
                    for a_, b_, c_ in itertools.combinations(sext, 3)
                ):
                    has_conic = True
                    break
        if has_conic:
            irreducible_conic_rows += 1

        if row["success"] == 1:
            certified_total += 1
            by_r[r_key]["certified"] += 1
            by_r[r_key]["recovered_selected"] += row["dl_recovered"]
            by_prime[p_key]["certified"] += 1
            by_lift[lift_key]["certified"] += 1

            fixed = transport_to_fixed_flex(row["relation"], row["origin_pair"])
            supp = [i for i, val in enumerate(fixed) if val != 0]
            if is_collinear_alias(row["relation"], row["origin_pair"], points):
                collinear_certified += 1
                by_r[r_key]["collinear_certified"] += 1
                by_prime[p_key]["collinear_certified"] += 1
                by_lift[lift_key]["collinear_certified"] += 1
            else:
                cubic_dependent_certified += 1
                by_r[r_key]["cubic_dependent_certified"] += 1
                by_prime[p_key]["cubic_dependent_certified"] += 1
                by_lift[lift_key]["cubic_dependent_certified"] += 1
                cubic_dependent_examples.append(
                    {
                        "p": row["p"],
                        "family": row["family"],
                        "lift": row["lift"],
                        "r": row["r"],
                        "idx": row["idx"],
                        "origin_pair": row["origin_pair"],
                        "local_relation": row["relation"],
                        "fixed_flex_relation": fixed,
                        "support_points": {str(i): list(points[i]) for i in supp},
                        "multipliers": multipliers,
                        "dl_recovered": row["dl_recovered"],
                    }
                )

    for (r_val, p_val, lift_val), pairs in sorted(height_buckets.items()):
        c_bits = [c for c, _ in pairs]
        d_bits = [d for _, d in pairs]
        med_c = statistics.median(c_bits)
        med_d = statistics.median(d_bits)
        height_scaling[f"r={r_val}/p={p_val}/lift={lift_val}"] = {
            "count": len(pairs),
            "median_coefficient_bits": med_c,
            "median_discriminant_bits": med_d,
            "coef_bits_per_log2_p": round(med_c / math.log2(p_val), 4),
            "disc_bits_per_log2_p": round(med_d / math.log2(p_val), 4),
        }

    return {
        "schema": "cryptanalysis.xedni-nov17-panel-decomposition/v1",
        "source_rows_path": "research/xedni_plane_group_20261117/run/rows.jsonl",
        "source_rows_sha256": actual_sha,
        "scheduled_rows": 1600,
        "eligible_rows": ok_rows,
        "certified_relations": certified_total,
        "pre_lift_collinear_aliases": collinear_certified,
        "genuine_cubic_dependent_relations": cubic_dependent_certified,
        "r789_certified_relations": sum(by_r[str(r)]["certified"] for r in (7, 8, 9)),
        "r789_collinear_aliases": sum(by_r[str(r)]["collinear_certified"] for r in (7, 8, 9)),
        "r789_cubic_dependent_relations": sum(
            by_r[str(r)]["cubic_dependent_certified"] for r in (7, 8, 9)
        ),
        "rows_with_any_pre_lift_collinear_triple": rows_with_any_collinear,
        "rows_with_multiple_collinear_triples": rows_with_multi_collinear,
        "rows_with_target_bearing_collinear_triple": rows_with_target_collinear,
        "missed_pre_lift_collinear_rows": missed_collinear_rows,
        "irreducible_six_point_conic_rows": irreducible_conic_rows,
        "by_r": by_r,
        "by_prime": by_prime,
        "by_lift": by_lift,
        "height_scaling": height_scaling,
        "cubic_dependent_examples": cubic_dependent_examples,
    }


def selftest() -> dict:
    # Positive control: five-term origin-local vector transports to (1,1,1) collinear triple.
    local = [-1, -1, 1, 0, 1, 0, 0, 0, 1]
    fixed = transport_to_fixed_flex(local, [0, 1])
    assert fixed == [0, 0, 1, 0, 1, 0, 0, 0, 1]
    assert det3((0, 1, 1), (2, 5, 1), (4, 9, 1)) == 0
    assert det3((0, 1, 1), (2, 5, 1), (4, 10, 1)) != 0
    summary = analyze_panel()
    assert summary["eligible_rows"] == 1205
    assert summary["certified_relations"] == 67
    assert summary["pre_lift_collinear_aliases"] == 66
    assert summary["genuine_cubic_dependent_relations"] == 1
    assert summary["r789_certified_relations"] == 58
    assert summary["r789_collinear_aliases"] == 58
    assert summary["r789_cubic_dependent_relations"] == 0
    assert summary["missed_pre_lift_collinear_rows"] == 0
    return {"status": "PASS", "certified": 67, "collinear_aliases": 66, "cubic_dependent": 1}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("selftest")
    run_cmd = sub.add_parser("run")
    run_cmd.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "selftest":
        print(json.dumps(selftest(), sort_keys=True))
        return
    report = analyze_panel()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "eligible": report["eligible_rows"],
                "certified": report["certified_relations"],
                "collinear_aliases": report["pre_lift_collinear_aliases"],
                "cubic_dependent": report["genuine_cubic_dependent_relations"],
                "r789_cubic_dependent": report["r789_cubic_dependent_relations"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
