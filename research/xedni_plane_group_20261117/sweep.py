#!/usr/bin/env python3
"""Prospective r=7..9 Xedni plane-cubic sweep; see PROTOCOL.md."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[2]
OLD_SWEEP = ROOT / "research/xedni_lift_success_20261112/sweep.py"
SPEC = importlib.util.spec_from_file_location("xedni_lift_success_20261112", OLD_SWEEP)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {OLD_SWEEP}")
old = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(old)

NBOX = 2
RADIUS = 1
Q_PRIMES = (2**61 - 1, 2**89 - 1, 2**107 - 1)
MONOMIALS = (
    (3, 0, 0),
    (2, 1, 0),
    (1, 2, 0),
    (0, 3, 0),
    (2, 0, 1),
    (1, 1, 1),
    (0, 2, 1),
    (1, 0, 2),
    (0, 1, 2),
    (0, 0, 3),
)


def incidence(point):
    x, y, z = point
    return [
        x**3,
        x * x * y,
        x * y * y,
        y**3,
        x * x * z,
        x * y * z,
        y * y * z,
        x * z * z,
        y * z * z,
        z**3,
    ]


def primitive(point, mod=None):
    point = tuple(int(v) for v in point)
    if mod is not None:
        point = tuple(v % mod for v in point)
        if not any(point):
            raise ValueError("zero projective point")
        first = next(v for v in point if v)
        inv = pow(first, -1, mod)
        return tuple(v * inv % mod for v in point)
    if not any(point):
        raise ValueError("zero projective point")
    g = 0
    for value in point:
        g = math.gcd(g, value)
    point = tuple(v // g for v in point)
    if next(v for v in point if v) < 0:
        point = tuple(-v for v in point)
    return point


def on_cubic(coefficients, point, mod=None):
    value = sum(a * b for a, b in zip(coefficients, incidence(point)))
    return value % mod == 0 if mod else value == 0


def gradient(coefficients, point, mod=None):
    c = coefficients
    x, y, z = point
    values = (
        3 * c[0] * x * x
        + 2 * c[1] * x * y
        + c[2] * y * y
        + 2 * c[4] * x * z
        + c[5] * y * z
        + c[7] * z * z,
        c[1] * x * x
        + 2 * c[2] * x * y
        + 3 * c[3] * y * y
        + c[5] * x * z
        + 2 * c[6] * y * z
        + c[8] * z * z,
        c[4] * x * x
        + c[5] * x * y
        + c[6] * y * y
        + 2 * c[7] * x * z
        + 2 * c[8] * y * z
        + 3 * c[9] * z * z,
    )
    return tuple(v % mod for v in values) if mod else values


def multiply_forms(a, b, mod=None):
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] += x * y
            if mod:
                out[i + j] %= mod
    return out


def restriction(coefficients, p, q, mod=None):
    result = [0, 0, 0, 0]
    for coefficient, exponents in zip(coefficients, MONOMIALS):
        term = [1]
        for coordinate, exponent in enumerate(exponents):
            for _ in range(exponent):
                term = multiply_forms(term, [p[coordinate], q[coordinate]], mod)
        for i, value in enumerate(term):
            result[i] += coefficient * value
            if mod:
                result[i] %= mod
    return tuple(result)


def cross_nonzero(p, q, mod=None):
    cross = (
        p[1] * q[2] - p[2] * q[1],
        p[2] * q[0] - p[0] * q[2],
        p[0] * q[1] - p[1] * q[0],
    )
    return any(v % mod for v in cross) if mod else any(cross)


def combine(a, p, b, q, mod=None):
    return primitive((a * p[i] + b * q[i] for i in range(3)), mod)


def third_intersection(coefficients, p, q, mod=None):
    p, q = primitive(p, mod), primitive(q, mod)
    if not on_cubic(coefficients, p, mod) or not on_cubic(coefficients, q, mod):
        raise ValueError("third intersection endpoint is off the cubic")
    if p != q:
        binary = restriction(coefficients, p, q, mod)
        return combine(binary[2], p, -binary[1], q, mod)

    gx, gy, gz = gradient(coefficients, p, mod)
    candidates = ((gy, -gx, 0), (gz, 0, -gx), (0, gz, -gy))
    auxiliary = None
    for candidate in candidates:
        nonzero = any(v % mod for v in candidate) if mod else any(candidate)
        if not nonzero:
            continue
        candidate = primitive(candidate, mod)
        if cross_nonzero(p, candidate, mod):
            auxiliary = candidate
            break
    if auxiliary is None:
        raise ValueError("failed to parameterize tangent")
    binary = restriction(coefficients, p, auxiliary, mod)
    return combine(binary[3], p, -binary[2], auxiliary, mod)


def group_add(coefficients, origin, p, q, mod=None):
    residual = third_intersection(coefficients, p, q, mod)
    return third_intersection(coefficients, residual, origin, mod)


def group_neg(coefficients, origin, point, mod=None):
    tangent_residual = third_intersection(coefficients, origin, origin, mod)
    return third_intersection(coefficients, point, tangent_residual, mod)


def group_mul(coefficients, origin, scalar, point, mod=None):
    if scalar < 0:
        return group_mul(coefficients, origin, -scalar, group_neg(coefficients, origin, point, mod), mod)
    result = primitive(origin, mod)
    addend = primitive(point, mod)
    while scalar:
        if scalar & 1:
            result = group_add(coefficients, origin, result, addend, mod)
        scalar >>= 1
        if scalar:
            addend = group_add(coefficients, origin, addend, addend, mod)
    return result


def choose_chord_origin(coefficients, points, known_count):
    """First known-point pair whose chord residual is not a selected point."""
    selected = {primitive(point) for point in points}
    for left in range(known_count):
        for right in range(left + 1, known_count):
            origin = third_intersection(coefficients, points[left], points[right])
            if origin not in selected:
                return origin, left, right
    raise ValueError("no chord residual distinct from the selected points")


def relation_sum(coefficients, origin, relation, points, mod=None):
    total = primitive(origin, mod)
    for scalar, point in zip(relation, points):
        total = group_add(
            coefficients,
            origin,
            total,
            group_mul(coefficients, origin, scalar, point, mod),
            mod,
        )
    return total


def find_relation(points, coefficients, origin, discriminant, bound):
    q = next(q for q in Q_PRIMES if discriminant % q)
    cq = tuple(c % q for c in coefficients)
    oq = primitive(origin, q)
    pq = [primitive(point, q) for point in points]
    tables = []
    for point in pq:
        tables.append(
            {
                scalar: group_mul(cq, oq, scalar, point, q)
                for scalar in range(-bound, bound + 1)
            }
        )
    half = (len(points) + 1) // 2

    def enumerate_sums(indices):
        rows = [((), oq)]
        for index in indices:
            rows = [
                (
                    relation + (scalar,),
                    group_add(cq, oq, total, tables[index][scalar], q),
                )
                for relation, total in rows
                for scalar in range(-bound, bound + 1)
            ]
        return rows

    left = {}
    for relation, total in enumerate_sums(range(half)):
        left.setdefault(total, []).append(relation)
    candidates = []
    for relation, total in enumerate_sums(range(half, len(points))):
        opposite = group_neg(cq, oq, total, q)
        for prefix in left.get(opposite, ()):
            candidate = prefix + relation
            if any(candidate):
                candidates.append(candidate)
    candidates.sort(key=lambda v: (sum(map(abs, v)), v))
    for candidate in candidates:
        if relation_sum(coefficients, origin, candidate, points) == origin:
            return candidate
    return None


def source_recovery(relation, multipliers, origin_multiplier, order):
    residue = sum(
        scalar * (multiplier - origin_multiplier)
        for scalar, multiplier in zip(relation, multipliers)
    ) % order
    target_coefficient = relation[-1] % order
    if math.gcd(target_coefficient, order) != 1:
        return residue, None
    known_sum = sum(
        scalar * (multiplier - origin_multiplier)
        for scalar, multiplier in zip(relation[:-1], multipliers[:-1])
    )
    recovered = (origin_multiplier - known_sum * pow(target_coefficient, -1, order)) % order
    return residue, recovered


def run_trial(binary, tempdir, p, family, lift, r, index, master, pools):
    rng = random.Random(f"{master}|{p}|{family}|{lift}|{r}|{index}")
    curves, square_table = pools[(p, family)]
    a, b, cardinality = curves[index % len(curves)]
    row = {
        "p": p,
        "family": family,
        "lift": lift,
        "r": r,
        "idx": index,
        "a": a,
        "b": b,
        "curve_order": cardinality,
        "status": "",
        "success": 0,
    }
    for _ in range(200):
        x = rng.randrange(p)
        ordinates = square_table.get((x**3 + a * x + b) % p)
        if ordinates:
            break
    else:
        row["status"] = "no_point"
        return row
    base = (x, rng.choice(ordinates))
    order = old.divisors_order(cardinality, base, a, p)
    row["subgroup_order"] = order
    if order < 2 * r + 1:
        row["status"] = "small_order"
        return row
    classes, multipliers = set(), []
    while len(multipliers) < r - 1:
        multiplier = rng.randrange(1, order)
        if multiplier in classes or order - multiplier in classes:
            continue
        classes.add(multiplier)
        multipliers.append(multiplier)
    while True:
        target = rng.randrange(1, order)
        if target not in classes and order - target not in classes:
            break
    multipliers.append(target)
    finite_points = [old.ec_mul_p(m, base, a, p) for m in multipliers]
    if any(point is None for point in finite_points):
        row["status"] = "identity"
        return row
    balanced = lambda value: value - p if value > p // 2 else value
    points = []
    for px, py in finite_points:
        px, py = balanced(px), balanced(py)
        if lift == "wide":
            px += p * rng.choice((-1, 0, 1))
            py += p * rng.choice((-1, 0, 1))
        points.append((px, py, 1))
    matrix = [incidence(point) for point in points]
    source_coefficients = [1, 0, 0, 0, 0, 0, -1, a, 0, b]
    values = [sum(x * y for x, y in zip(row_, source_coefficients)) for row_ in matrix]
    if any(value % p for value in values):
        row["status"] = "internal_not_on_curve"
        return row
    solution = old.solve_affine(matrix, [-value // p for value in values], 10)
    if solution is None:
        row["status"] = "no_integer_solution"
        return row
    particular_delta, kernel, rank = solution
    if rank != r:
        row["status"] = "rank_deficient"
        return row
    particular = [source_coefficients[i] + p * particular_delta[i] for i in range(10)]
    directions = [[p * value for value in vector] for vector in kernel]
    payload = {
        "particular": [str(value) for value in particular],
        "directions": [[str(value) for value in vector] for vector in directions],
        "projective_points": [[str(value) for value in point] for point in points],
        "congruence_modulus": str(p),
    }
    input_path = Path(tempdir) / f"input-{os.getpid()}.json"
    input_path.write_text(json.dumps(payload))
    completed = subprocess.run(
        [
            binary,
            "--json",
            "xedni-lift",
            "--model",
            "plane-cubic",
            "--input",
            str(input_path),
            "--radius",
            str(RADIUS),
            "--max-candidates",
            str(3 ** len(directions)),
        ],
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        row["status"] = "lift_error"
        row["error"] = (completed.stderr or completed.stdout)[-300:]
        return row
    result = json.loads(completed.stdout)["result"]
    coefficients = [int(value) for value in result["optimized_coefficients"]]
    row["coefficient_bits"] = result["optimized_score"]["coefficient_height_bits"]
    row["discriminant_bits"] = result["optimized_score"]["discriminant_bits"]
    discriminant = int(result["optimized_score"]["discriminant"])
    if not all(on_cubic(coefficients, point) for point in points):
        row["status"] = "lift_cert_failed"
        return row
    if any((coefficients[i] - source_coefficients[i]) % p for i in range(10)):
        row["status"] = "lift_cert_failed"
        return row
    try:
        origin, origin_left, origin_right = choose_chord_origin(coefficients, points, r - 1)
        origin_multiplier = -(multipliers[origin_left] + multipliers[origin_right])
        shifted = [(m - origin_multiplier) % order for m in multipliers]
        row["fp_rel"] = int(old.fp_relation_exists(shifted, order, NBOX))
        relation = find_relation(points, coefficients, origin, discriminant, NBOX)
    except (ArithmeticError, ValueError) as error:
        row["status"] = "group_error"
        row["error"] = str(error)
        return row
    row["origin_pair"] = [origin_left, origin_right]
    row["status"] = "ok"
    if relation is None:
        return row
    exact_sum = relation_sum(coefficients, origin, relation, points)
    residue, recovered = source_recovery(relation, multipliers, origin_multiplier, order)
    if exact_sum != origin or residue:
        row["status"] = "relation_cert_failed"
        return row
    row["success"] = 1
    row["relation"] = list(relation)
    row["weight"] = sum(value != 0 for value in relation)
    row["dl_recovered"] = int(recovered == target % order)
    return row


def selftest():
    coefficients = (1, 0, 0, 0, 0, 0, -1, -1, 0, 1)
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
    points = [primitive(map(int, point)) for point in raw_points]
    assert all(on_cubic(coefficients, point) for point in points)
    origin, origin_left, origin_right = choose_chord_origin(coefficients, points, 8)
    assert (origin_left, origin_right) == (0, 1)
    relation = (0, 0, 2, 0, 0, 0, 0, 0, -1)
    assert relation_sum(coefficients, origin, relation, points) == origin
    assert relation_sum(coefficients, origin, relation, points, Q_PRIMES[0]) == primitive(
        origin, Q_PRIMES[0]
    )
    residue, recovered = source_recovery(relation, list(range(1, 10)), -3, 73)
    assert residue == 0 and recovered == 9
    mutated = list(relation)
    mutated[2] += 1
    assert relation_sum(coefficients, origin, mutated, points) != origin
    found = find_relation(points, coefficients, origin, 635904, NBOX)
    assert found is not None
    return {"status": "PASS", "found_relation": list(found)}


def main():
    parser = argparse.ArgumentParser()
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("selftest")
    run = subcommands.add_parser("run")
    run.add_argument("--binary", required=True)
    run.add_argument("--output", required=True)
    run.add_argument("--master", required=True)
    run.add_argument("--primes", required=True)
    run.add_argument("--families", required=True)
    run.add_argument("--lifts", required=True)
    run.add_argument("--r-values", required=True)
    run.add_argument("--trials", type=int, required=True)
    args = parser.parse_args()
    if args.command == "selftest":
        print(json.dumps(selftest(), sort_keys=True))
        return

    primes = tuple(map(int, args.primes.split(",")))
    families = tuple(args.families.split(","))
    lifts = tuple(args.lifts.split(","))
    r_values = tuple(map(int, args.r_values.split(",")))
    if not all(old.is_prime(prime) for prime in primes):
        raise SystemExit("non-prime in --primes")
    pools = {
        (prime, family): old.curve_pool(
            prime,
            family,
            random.Random(f"{args.master}|pool|{prime}|{family}"),
        )
        for prime in primes
        for family in families
    }
    jobs = [
        (prime, family, lift, r, index)
        for prime in primes
        for family in families
        for lift in lifts
        for r in r_values
        for index in range(args.trials)
    ]
    started = time.time()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="xedni-r9-") as tempdir, open(
        args.output, "w", encoding="utf-8"
    ) as output:
        for job_index, (prime, family, lift, r, index) in enumerate(jobs):
            row = run_trial(
                args.binary,
                tempdir,
                prime,
                family,
                lift,
                r,
                index,
                args.master,
                pools,
            )
            output.write(json.dumps(row, sort_keys=True) + "\n")
            output.flush()
            if job_index % 25 == 0:
                print(f"{job_index + 1}/{len(jobs)}", flush=True)
    print(json.dumps({"rows": len(jobs), "seconds": time.time() - started}, sort_keys=True))


if __name__ == "__main__":
    main()
