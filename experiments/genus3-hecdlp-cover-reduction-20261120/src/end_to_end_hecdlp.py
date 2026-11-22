#!/usr/bin/env python3
"""Complete toy genus-3 HECDLP solves with measured index-calculus stages.

The curves have prime-order Jacobians certified by stored point counts over
F_q, F_(q^2), and F_(q^3).  Cantor arithmetic, smooth-divisor relation
collection, dense modular linear algebra, individual-log descent, and a
same-group Pollard-rho baseline are all executed and verified.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import random
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import sympy


IDENTITY = ((1,), (0,))


@dataclass(frozen=True)
class Curve:
    prime: int
    a: int
    b: int
    point_counts: tuple[int, int, int]
    jacobian_order: int

    @property
    def f(self):
        return (self.b, self.a, 0, 0, 0, 0, 0, 1)


CURVES = (
    Curve(17, 2, 1, (23, 303, 4925), 6763),
    Curve(19, 4, 4, (27, 359, 6927), 9923),
    Curve(47, 2, 4, (47, 2239, 103643), 102259),
    Curve(53, 5, 4, (53, 2859, 147791), 147031),
    Curve(67, 4, 4, (85, 4623, 300199), 393203),
    Curve(83, 2, 5, (71, 7019, 571409), 493403),
    Curve(101, 2, 8, (113, 10447, 1031057), 1163011),
)


def trim(poly, prime):
    values = [int(value) % prime for value in poly]
    while len(values) > 1 and values[-1] == 0:
        values.pop()
    return tuple(values or [0])


def degree(poly):
    return len(poly) - 1


def add(left, right, prime):
    return trim(
        [
            (left[i] if i < len(left) else 0)
            + (right[i] if i < len(right) else 0)
            for i in range(max(len(left), len(right)))
        ],
        prime,
    )


def neg(poly, prime):
    return trim([-value for value in poly], prime)


def sub(left, right, prime):
    return add(left, neg(right, prime), prime)


def scale(poly, scalar, prime):
    return trim([scalar * value for value in poly], prime)


def mul(left, right, prime):
    result = [0] * (len(left) + len(right) - 1)
    for i, x in enumerate(left):
        for j, y in enumerate(right):
            result[i + j] = (result[i + j] + x * y) % prime
    return trim(result, prime)


def divmod_poly(numerator, denominator, prime):
    numerator = list(trim(numerator, prime))
    denominator = trim(denominator, prime)
    if denominator == (0,):
        raise ZeroDivisionError
    quotient = [0] * max(1, len(numerator) - len(denominator) + 1)
    inverse = pow(denominator[-1], -1, prime)
    while len(numerator) >= len(denominator) and any(numerator):
        shift = len(numerator) - len(denominator)
        coefficient = numerator[-1] * inverse % prime
        quotient[shift] = coefficient
        for index, value in enumerate(denominator):
            numerator[shift + index] = (
                numerator[shift + index] - coefficient * value
            ) % prime
        while len(numerator) > 1 and numerator[-1] == 0:
            numerator.pop()
    return trim(quotient, prime), trim(numerator, prime)


def exact_div(numerator, denominator, prime):
    quotient, remainder = divmod_poly(numerator, denominator, prime)
    if remainder != (0,):
        raise ArithmeticError("non-exact polynomial division")
    return quotient


def monic(poly, prime):
    poly = trim(poly, prime)
    if poly == (0,):
        raise ZeroDivisionError
    return scale(poly, pow(poly[-1], -1, prime), prime)


def xgcd(left, right, prime):
    r0, r1 = trim(left, prime), trim(right, prime)
    s0, s1 = (1,), (0,)
    t0, t1 = (0,), (1,)
    while r1 != (0,):
        quotient, remainder = divmod_poly(r0, r1, prime)
        r0, r1 = r1, remainder
        s0, s1 = s1, sub(s0, mul(quotient, s1, prime), prime)
        t0, t1 = t1, sub(t0, mul(quotient, t1, prime), prime)
    inverse = pow(r0[-1], -1, prime)
    return (
        scale(r0, inverse, prime),
        scale(s0, inverse, prime),
        scale(t0, inverse, prime),
    )


def evaluate(poly, value, prime):
    result = 0
    for coefficient in reversed(poly):
        result = (result * value + coefficient) % prime
    return result


def reduce_divisor(divisor, curve):
    p, f = curve.prime, curve.f
    u, v = divisor
    u = monic(u, p)
    v = divmod_poly(v, u, p)[1]
    while degree(u) > 3:
        quotient = exact_div(sub(f, mul(v, v, p), p), u, p)
        u = monic(quotient, p)
        v = divmod_poly(neg(v, p), u, p)[1]
    u = monic(u, p)
    v = divmod_poly(v, u, p)[1]
    if divmod_poly(sub(f, mul(v, v, p), p), u, p)[1] != (0,):
        raise ArithmeticError("invalid reduced Mumford divisor")
    return u, v


def compose(left, right, curve):
    p, f = curve.prime, curve.f
    u1, v1 = left
    u2, v2 = right
    d12, bezout1, bezout2 = xgcd(u1, u2, p)
    d, combine, third = xgcd(d12, add(v1, v2, p), p)
    h1 = mul(combine, bezout1, p)
    h2 = mul(combine, bezout2, p)
    numerator = add(
        add(mul(mul(h1, u1, p), v2, p), mul(mul(h2, u2, p), v1, p), p),
        mul(third, add(mul(v1, v2, p), f, p), p),
        p,
    )
    v = exact_div(numerator, d, p)
    u = exact_div(mul(u1, u2, p), mul(d, d, p), p)
    return reduce_divisor((u, divmod_poly(v, u, p)[1]), curve)


def negate_divisor(divisor, curve):
    return divisor[0], neg(divisor[1], curve.prime)


def scalar_mul(scalar, divisor, curve):
    result, addend = IDENTITY, divisor
    while scalar:
        if scalar & 1:
            result = compose(result, addend, curve)
        addend = compose(addend, addend, curve)
        scalar >>= 1
    return result


def point_divisor(x, y, curve):
    return ((-x % curve.prime, 1), (y % curve.prime,))


def point_count_order(curve):
    q = curve.prime
    n1, n2, n3 = curve.point_counts
    power_sums = (q + 1 - n1, q**2 + 1 - n2, q**3 + 1 - n3)
    s1, s2, s3 = power_sums
    e1 = s1
    e2 = (s1 * s1 - s2) // 2
    e3 = (s1**3 - 3 * s1 * s2 + 2 * s3) // 6
    coefficients = (1, -e1, e2, -e3, q * e2, -(q**2) * e1, q**3)
    return sum(coefficients), coefficients


def factor_base(curve):
    p = curve.prime
    result = []
    for x in range(p):
        rhs = evaluate(curve.f, x, p)
        roots = [y for y in range(p) if y * y % p == rhs]
        if not roots:
            continue
        if len(roots) != 2 or roots[0] == 0:
            raise ArithmeticError("unexpected rational Weierstrass point")
        result.append((x, min(roots[0], roots[1])))
    return tuple(result)


def split_vector(divisor, base, curve):
    p = curve.prime
    u, v = divisor
    remaining = u
    roots = []
    for x in range(p):
        linear = (-x % p, 1)
        while degree(remaining) > 0 and evaluate(remaining, x, p) == 0:
            remaining = exact_div(remaining, linear, p)
            roots.append(x)
    if degree(remaining) != 0 or len(roots) != degree(u):
        return None
    positions = {x: (index, y) for index, (x, y) in enumerate(base)}
    vector = [0] * len(base)
    for root in roots:
        if root not in positions:
            return None
        index, canonical_y = positions[root]
        y = evaluate(v, root, p)
        if y == canonical_y:
            vector[index] += 1
        elif y == -canonical_y % p:
            vector[index] -= 1
        else:
            raise ArithmeticError("Mumford root has inconsistent y-coordinate")
    return tuple(value % curve.jacobian_order for value in vector)


def vector_divisor(vector, base, curve):
    result = IDENTITY
    order = curve.jacobian_order
    for coefficient, (x, y) in zip(vector, base):
        signed = coefficient if coefficient <= order // 2 else coefficient - order
        point = point_divisor(x, y, curve)
        if signed < 0:
            point = negate_divisor(point, curve)
        for _ in range(abs(signed)):
            result = compose(result, point, curve)
    return result


def rank_mod(matrix, prime):
    work = [[value % prime for value in row] for row in matrix]
    rank = 0
    for column in range(len(work[0]) if work else 0):
        pivot = next((row for row in range(rank, len(work)) if work[row][column]), None)
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        inverse = pow(work[rank][column], -1, prime)
        work[rank] = [value * inverse % prime for value in work[rank]]
        for row in range(len(work)):
            if row == rank or not work[row][column]:
                continue
            factor = work[row][column]
            work[row] = [
                (x - factor * y) % prime for x, y in zip(work[row], work[rank])
            ]
        rank += 1
        if rank == len(work):
            break
    return rank


def solve_square(matrix, rhs, prime):
    size = len(rhs)
    work = [
        [value % prime for value in matrix[row]] + [rhs[row] % prime]
        for row in range(size)
    ]
    for column in range(size):
        pivot = next((row for row in range(column, size) if work[row][column]), None)
        if pivot is None:
            raise ArithmeticError("singular relation matrix")
        work[column], work[pivot] = work[pivot], work[column]
        inverse = pow(work[column][column], -1, prime)
        work[column] = [value * inverse % prime for value in work[column]]
        for row in range(size):
            if row == column or not work[row][column]:
                continue
            factor = work[row][column]
            work[row] = [
                (x - factor * y) % prime
                for x, y in zip(work[row], work[column])
            ]
    return tuple(work[index][-1] for index in range(size))


class SparseEchelon:
    """Online sparse row echelon form with a solved right-hand side."""

    def __init__(self, columns, prime):
        self.columns = columns
        self.prime = prime
        self.pivots = {}
        self.maximum_pivot_nonzeros = 0

    @property
    def rank(self):
        return len(self.pivots)

    def add(self, dense_row, rhs):
        p = self.prime
        row = {index: value % p for index, value in enumerate(dense_row) if value % p}
        rhs %= p
        while row:
            column = min(row)
            if column not in self.pivots:
                inverse = pow(row[column], -1, p)
                row = {index: value * inverse % p for index, value in row.items()}
                rhs = rhs * inverse % p
                self.pivots[column] = (row, rhs)
                self.maximum_pivot_nonzeros = max(
                    self.maximum_pivot_nonzeros, len(row)
                )
                return True
            pivot, pivot_rhs = self.pivots[column]
            factor = row[column]
            for index, value in pivot.items():
                updated = (row.get(index, 0) - factor * value) % p
                if updated:
                    row[index] = updated
                else:
                    row.pop(index, None)
            rhs = (rhs - factor * pivot_rhs) % p
        if rhs:
            raise ArithmeticError("inconsistent relation row")
        return False

    def solve(self):
        if self.rank != self.columns:
            raise ArithmeticError("sparse relation matrix is not full rank")
        solution = [0] * self.columns
        for column in sorted(self.pivots, reverse=True):
            row, rhs = self.pivots[column]
            solution[column] = (
                rhs
                - sum(
                    value * solution[index]
                    for index, value in row.items()
                    if index != column
                )
            ) % self.prime
        return tuple(solution)

    def pivot_nonzeros(self):
        return sum(len(row) for row, _ in self.pivots.values())


def divisor_partition(divisor):
    u, v = divisor
    return (
        sum((index + 1) * value for index, value in enumerate(u))
        + 17 * sum((index + 1) * value for index, value in enumerate(v))
    ) % 3


def rho_step(state, generator, target, curve):
    divisor, alpha, beta = state
    order = curve.jacobian_order
    branch = divisor_partition(divisor)
    if branch == 0:
        return compose(divisor, target, curve), alpha, (beta + 1) % order
    if branch == 1:
        return compose(divisor, divisor, curve), 2 * alpha % order, 2 * beta % order
    return compose(divisor, generator, curve), (alpha + 1) % order, beta


def pollard_rho_jacobian(generator, target, curve, rng, max_restarts=32):
    order = curve.jacobian_order
    operations = 0
    for restart in range(max_restarts):
        alpha, beta = rng.randrange(order), rng.randrange(order)
        state = compose(
            scalar_mul(alpha, generator, curve), scalar_mul(beta, target, curve), curve
        )
        tortoise = (state, alpha, beta)
        hare = tortoise
        for _ in range(10 * math.isqrt(order) + 100):
            tortoise = rho_step(tortoise, generator, target, curve)
            hare = rho_step(rho_step(hare, generator, target, curve), generator, target, curve)
            operations += 3
            if tortoise[0] != hare[0]:
                continue
            numerator = (hare[1] - tortoise[1]) % order
            denominator = (tortoise[2] - hare[2]) % order
            if denominator:
                logarithm = numerator * pow(denominator, -1, order) % order
                if scalar_mul(logarithm, generator, curve) == target:
                    return logarithm, operations, restart
            break
    raise RuntimeError("Jacobian rho exhausted restarts")


def benchmark_curve(curve, seed, target_trials=20):
    order_from_counts, l_polynomial = point_count_order(curve)
    if order_from_counts != curve.jacobian_order or not sympy.isprime(curve.jacobian_order):
        raise AssertionError("stored prime-order certificate failed")
    base = factor_base(curve)
    generator = point_divisor(*base[0], curve)
    if generator == IDENTITY or scalar_mul(curve.jacobian_order, generator, curve) != IDENTITY:
        raise AssertionError("generator order certificate failed")
    rng = random.Random(seed ^ curve.prime)

    relation_started = time.perf_counter()
    rows, rhs = [], []
    sparse = SparseEchelon(len(base), curve.jacobian_order)
    candidates = smooth = 0
    sparse_online_seconds = 0.0
    input_nonzeros = 0
    while sparse.rank < len(base):
        scalar = rng.randrange(1, curve.jacobian_order)
        divisor = scalar_mul(scalar, generator, curve)
        candidates += 1
        vector = split_vector(divisor, base, curve)
        if vector is None:
            continue
        smooth += 1
        if vector_divisor(vector, base, curve) != divisor:
            raise AssertionError("smooth relation failed divisor reconstruction")
        input_nonzeros += sum(bool(value) for value in vector)
        sparse_started = time.perf_counter()
        independent = sparse.add(vector, scalar)
        sparse_online_seconds += time.perf_counter() - sparse_started
        if independent:
            rows.append(vector)
            rhs.append(scalar)
    relation_seconds = time.perf_counter() - relation_started

    sparse_started = time.perf_counter()
    logs = sparse.solve()
    sparse_solve_seconds = time.perf_counter() - sparse_started
    dense_started = time.perf_counter()
    dense_logs = solve_square(rows, rhs, curve.jacobian_order)
    dense_control_seconds = time.perf_counter() - dense_started
    if logs != dense_logs:
        raise AssertionError("sparse and dense relation solutions disagree")
    for logarithm, point in zip(logs, base):
        if scalar_mul(logarithm, generator, curve) != point_divisor(*point, curve):
            raise AssertionError("factor-base logarithm failed verification")

    individual_times, individual_attempts = [], []
    rho_times, rho_operations = [], []
    recovered_all = True
    measured_crossover_target = None
    cumulative_individual = 0.0
    cumulative_rho = 0.0
    precomputation_seconds = relation_seconds + sparse_solve_seconds
    for trial in range(1, target_trials + 1):
        secret = rng.randrange(1, curve.jacobian_order)
        target = scalar_mul(secret, generator, curve)
        started = time.perf_counter()
        attempts = 0
        while True:
            offset = rng.randrange(curve.jacobian_order)
            divisor = compose(target, scalar_mul(offset, generator, curve), curve)
            attempts += 1
            vector = split_vector(divisor, base, curve)
            if vector is None:
                continue
            recovered = (
                sum(coefficient * logarithm for coefficient, logarithm in zip(vector, logs))
                - offset
            ) % curve.jacobian_order
            break
        individual_elapsed = time.perf_counter() - started
        individual_times.append(individual_elapsed)
        cumulative_individual += individual_elapsed
        individual_attempts.append(attempts)
        recovered_all &= recovered == secret

        rho_started = time.perf_counter()
        rho_log, operations, _ = pollard_rho_jacobian(generator, target, curve, rng)
        rho_elapsed = time.perf_counter() - rho_started
        rho_times.append(rho_elapsed)
        cumulative_rho += rho_elapsed
        rho_operations.append(operations)
        recovered_all &= rho_log == secret
        if (
            measured_crossover_target is None
            and precomputation_seconds + cumulative_individual <= cumulative_rho
        ):
            measured_crossover_target = trial
    if not recovered_all:
        raise AssertionError("an individual logarithm was not recovered")

    median_individual = statistics.median(individual_times)
    return {
        "field_size_q": curve.prime,
        "curve": f"y^2=x^7+{curve.a}*x+{curve.b}",
        "point_counts_q_q2_q3": list(curve.point_counts),
        "l_polynomial_coefficients_low_to_high": list(l_polynomial),
        "jacobian_order": curve.jacobian_order,
        "jacobian_order_prime": True,
        "factor_base_size": len(base),
        "relation_candidates": candidates,
        "smooth_relations": smooth,
        "independent_relations": len(rows),
        "relation_seconds": relation_seconds,
        "input_relation_matrix_density": input_nonzeros
        / (max(1, smooth) * len(base)),
        "sparse_online_elimination_seconds": sparse_online_seconds,
        "sparse_solve_seconds": sparse_solve_seconds,
        "sparse_pivot_nonzeros": sparse.pivot_nonzeros(),
        "sparse_maximum_pivot_row_nonzeros": sparse.maximum_pivot_nonzeros,
        "dense_control_seconds": dense_control_seconds,
        "sparse_dense_solutions_equal": True,
        "precomputation_seconds": precomputation_seconds,
        "target_trials": target_trials,
        "median_individual_descent_attempts": statistics.median(individual_attempts),
        "median_individual_descent_seconds": median_individual,
        "median_index_total_seconds": precomputation_seconds + median_individual,
        "measured_batch_index_seconds": precomputation_seconds
        + cumulative_individual,
        "measured_batch_rho_seconds": cumulative_rho,
        "measured_crossover_target": measured_crossover_target,
        "median_pollard_rho_jacobian_additions": statistics.median(rho_operations),
        "median_pollard_rho_seconds": statistics.median(rho_times),
        "all_factor_base_logs_verified": True,
        "all_target_logs_recovered": recovered_all,
    }


def fit_slope(rows, x_key, y_key):
    points = [(math.log(row[x_key]), math.log(row[y_key])) for row in rows]
    mean_x = statistics.fmean(x for x, _ in points)
    mean_y = statistics.fmean(y for _, y in points)
    return sum((x - mean_x) * (y - mean_y) for x, y in points) / sum(
        (x - mean_x) ** 2 for x, _ in points
    )


def run(seed=7333, target_trials=20):
    started = time.perf_counter()
    rows = [benchmark_curve(curve, seed, target_trials) for curve in CURVES]
    return {
        "format": "genus3-hecdlp-end-to-end-toy-benchmark-v2",
        "seed": seed,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "sympy": sympy.__version__,
        },
        "algorithm": {
            "jacobian_arithmetic": "exact Cantor arithmetic in Mumford representation",
            "relation_collection": "random multiples of G whose reduced u-polynomial splits over F_q",
            "linear_algebra": "online sparse echelon collection and sparse back-substitution, cross-checked against dense Gaussian elimination",
            "individual_log": "random-offset smooth descent using solved factor-base logarithms",
            "baseline": "Pollard rho on the same Jacobian and same target",
        },
        "rows": rows,
        "fitted_slopes": {
            "relation_candidates_vs_q": fit_slope(rows, "field_size_q", "relation_candidates"),
            "index_total_seconds_vs_q": fit_slope(rows, "field_size_q", "median_index_total_seconds"),
            "rho_jacobian_additions_vs_group_order": fit_slope(
                rows, "jacobian_order", "median_pollard_rho_jacobian_additions"
            ),
            "rho_seconds_vs_group_order": fit_slope(
                rows, "jacobian_order", "median_pollard_rho_seconds"
            ),
        },
        "measured_scope": "complete toy HECDLP solves, including relation collection, linear algebra, individual descent, and same-group rho",
        "scope_limits": [
            "small prime fields only; not a NIST-size computation",
            "hyperelliptic genus-3 Jacobians, not the unresolved signed map to the NIST plane-quartic quotient",
            "dense linear algebra is used at toy sizes; production index calculus would require sparse methods",
            "timing crossover at these sizes is not a cryptographic asymptotic claim",
        ],
        "total_seconds": time.perf_counter() - started,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=7333)
    parser.add_argument("--target-trials", type=int, default=20)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run(args.seed, args.target_trials)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
