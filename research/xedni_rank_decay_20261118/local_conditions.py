#!/usr/bin/env python3
"""Deterministic local-condition controls for the Xedni rank-decay panel.

This module constructs only small-prime control data.  It never constructs a
natural lifted curve over Q and never computes a rank outcome.
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
from typing import Any, Iterable


SCHEMA = "xedni.local-conditions/v1"
STATUS = "control_only_no_natural_rank_rows"
INCIDENCE_MODEL = "short_weierstrass_7"
MAX_EXECUTABLE_R = 6
ARMS = (
    "A_none",
    "B_reverse_mestre",
    "B_reverse_mestre_plus1",
    "B_reverse_mestre_plus2",
    "P_neutral_crt",
    "I_incompatible",
)


class LocalConditionError(RuntimeError):
    """A requested local system could not be certified."""


Point = tuple[int, int] | None


@dataclass(frozen=True)
class Curve:
    p: int
    a: int
    b: int


def primes_7_to_97() -> tuple[int, ...]:
    return tuple(n for n in range(7, 98) if _is_prime(n))


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    return all(n % d for d in range(2, math.isqrt(n) + 1))


def _seed_int(seed: str, *labels: object) -> int:
    payload = "|".join((seed, *(str(label) for label in labels))).encode()
    return int.from_bytes(hashlib.sha256(payload).digest(), "big")


def _factor(n: int) -> dict[int, int]:
    factors: dict[int, int] = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors


def _divisors(n: int) -> list[int]:
    values = [1]
    for prime, exponent in _factor(n).items():
        values = [value * prime**power for value in values for power in range(exponent + 1)]
    return sorted(value for value in values if value > 1)


def discriminant_core(curve: Curve) -> int:
    """Return 4a^3+27b^2 modulo p; nonzero exactly when the curve is smooth."""
    return (4 * curve.a**3 + 27 * curve.b**2) % curve.p


def is_nonsingular(curve: Curve) -> bool:
    return discriminant_core(curve) != 0


def curve_points(curve: Curve) -> list[Point]:
    if not is_nonsingular(curve):
        raise LocalConditionError("refusing to enumerate a singular curve")
    p = curve.p
    square_roots: dict[int, list[int]] = {}
    for y in range(p):
        square_roots.setdefault(y * y % p, []).append(y)
    points: list[Point] = [None]
    for x in range(p):
        rhs = (x**3 + curve.a * x + curve.b) % p
        points.extend((x, y) for y in square_roots.get(rhs, ()))
    return points


def on_curve(curve: Curve, point: Point) -> bool:
    if point is None:
        return True
    x, y = point
    return (y * y - x**3 - curve.a * x - curve.b) % curve.p == 0


def point_neg(curve: Curve, point: Point) -> Point:
    return None if point is None else (point[0], (-point[1]) % curve.p)


def point_add(curve: Curve, left: Point, right: Point) -> Point:
    p = curve.p
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    if x1 == x2 and (y1 + y2) % p == 0:
        return None
    if left == right:
        if y1 % p == 0:
            return None
        slope = (3 * x1 * x1 + curve.a) * pow(2 * y1, -1, p) % p
    else:
        slope = (y2 - y1) * pow((x2 - x1) % p, -1, p) % p
    x3 = (slope * slope - x1 - x2) % p
    y3 = (slope * (x1 - x3) - y1) % p
    return (x3, y3)


def point_mul(curve: Curve, scalar: int, point: Point) -> Point:
    if scalar < 0:
        return point_mul(curve, -scalar, point_neg(curve, point))
    total = None
    addend = point
    while scalar:
        if scalar & 1:
            total = point_add(curve, total, addend)
        addend = point_add(curve, addend, addend)
        scalar >>= 1
    return total


def point_order(curve: Curve, point: Point, group_order: int) -> int:
    if point is None:
        return 1
    order = group_order
    for prime, exponent in _factor(group_order).items():
        for _ in range(exponent):
            if point_mul(curve, order // prime, point) is not None:
                break
            order //= prime
    return order


def cyclic_generator(curve: Curve, points: list[Point]) -> Point:
    order = len(points)
    for point in points:
        if point is not None and point_order(curve, point, order) == order:
            return point
    return None


def projective(point: Point) -> tuple[int, int, int]:
    return (0, 1, 0) if point is None else (point[0], point[1], 1)


def general_cubic_incidence_row(point: Point, p: int) -> tuple[int, ...]:
    """The paper's ten-column general-plane-cubic row (diagnostic only)."""
    x, y, z = projective(point)
    return tuple(
        value % p
        for value in (
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
        )
    )


def weierstrass_incidence_row(point: Point, p: int) -> tuple[int, ...]:
    """The seven-column row in JKSST Section 3.2 for Weierstrass models.

    The point at infinity produces the zero row, so a full-rank tuple is
    necessarily affine.  This is the required executable incidence model.
    """
    x, y, z = projective(point)
    return tuple(
        value % p
        for value in (
            y * y * z,
            x * y * z,
            y * z * z,
            x**3,
            x * x * z,
            x * z * z,
            z**3,
        )
    )


# Compatibility alias for code that imported the original diagnostic helper.
# Construction never uses this ten-column row as its admission test.
incidence_row = general_cubic_incidence_row


def matrix_rank_mod(rows: Iterable[Iterable[int]], p: int) -> int:
    matrix = [[value % p for value in row] for row in rows]
    if not matrix:
        return 0
    rank = 0
    columns = len(matrix[0])
    for column in range(columns):
        pivot = next((i for i in range(rank, len(matrix)) if matrix[i][column]), None)
        if pivot is None:
            continue
        matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
        inverse = pow(matrix[rank][column], -1, p)
        matrix[rank] = [value * inverse % p for value in matrix[rank]]
        for i, row in enumerate(matrix):
            if i != rank and row[column]:
                multiple = row[column]
                matrix[i] = [
                    (value - multiple * pivot_value) % p
                    for value, pivot_value in zip(row, matrix[rank])
                ]
        rank += 1
        if rank == len(matrix):
            break
    return rank


def target_point_count(arm: str, prime: int) -> int | None:
    if arm not in ARMS:
        raise ValueError(f"unknown arm {arm!r}")
    if arm == "A_none":
        return None
    if arm == "P_neutral_crt":
        return prime + 1
    offset = {
        "B_reverse_mestre": 0,
        "B_reverse_mestre_plus1": 1,
        "B_reverse_mestre_plus2": 2,
        "I_incompatible": 0,
    }[arm]
    return prime + 1 - math.isqrt(4 * prime) + offset


def _selection_arm(arm: str) -> str:
    """P uses B's frozen prime schedule so its CRT cost is actually matched."""
    return "B_reverse_mestre" if arm in {"P_neutral_crt", "I_incompatible"} else arm


def eligible_primes(arm: str, r: int, pool: Iterable[int] = primes_7_to_97()) -> dict:
    accepted = []
    rejected = []
    seen: set[int] = set()
    for prime in pool:
        if isinstance(prime, bool) or not isinstance(prime, int):
            rejected.append({"prime": prime, "reason": "not_an_integer"})
            continue
        if prime in seen:
            rejected.append({"prime": prime, "reason": "duplicate_prime"})
            continue
        seen.add(prime)
        if prime < 7 or prime > 97 or not _is_prime(prime):
            rejected.append({"prime": prime, "reason": "outside_prime_pool"})
            continue
        selection_arm = _selection_arm(arm)
        count = target_point_count(selection_arm, prime)
        # O has a zero row in the seven-column Weierstrass matrix.  Full row
        # rank therefore requires r distinct affine points: #E - 1 >= r.
        if count is not None and count - 1 < r:
            rejected.append(
                {
                    "prime": prime,
                    "reason": "fewer_than_r_usable_affine_points",
                    "selection_arm": selection_arm,
                    "selection_point_count": count,
                    "usable_affine_points": count - 1,
                }
            )
            continue
        # For r=6 and #E=7 the six usable points are all three inverse
        # pairs.  Pair-sums span at most the three effective even-y columns
        # (the curve equation removes one), while pair-differences span the
        # two odd-y columns, so the seven-column row rank is at most five.
        if r == 6 and count == 7:
            rejected.append(
                {
                    "prime": prime,
                    "reason": "weierstrass_incidence_rank_at_most_5",
                    "selection_arm": selection_arm,
                    "selection_point_count": count,
                    "usable_affine_points": count - 1,
                }
            )
            continue
        accepted.append(prime)
    return {"accepted": accepted, "rejected": rejected}


def prime_prefix_for_product(arm: str, r: int, target_product: int) -> dict:
    if (
        isinstance(target_product, bool)
        or not isinstance(target_product, int)
        or target_product < 1
    ):
        raise ValueError("target_product must be positive")
    eligibility = eligible_primes(arm, r)
    chosen = []
    product = 1
    for prime in eligibility["accepted"]:
        if product >= target_product:
            break
        chosen.append(prime)
        product *= prime
    if product < target_product:
        raise LocalConditionError(
            f"prime pool through 97 reaches M={product}, below target {target_product}"
        )
    return {
        "target_product": target_product,
        "primes": chosen,
        "product": product,
        "eligibility_rejections": eligibility["rejected"],
    }


def _curve_candidate_order(prime: int, seed: str, arm: str) -> list[tuple[int, int]]:
    candidates = list(itertools.product(range(prime), repeat=2))
    # The incompatible known-negative is a mutation of B, not a separately
    # sampled curve system.
    curve_arm = "B_reverse_mestre" if arm == "I_incompatible" else arm
    random.Random(_seed_int(seed, curve_arm, prime, "curves")).shuffle(candidates)
    return candidates


def _find_local_curve(
    prime: int,
    arm: str,
    seed: str,
    max_attempts: int | None,
) -> tuple[Curve, list[Point], Point, list[dict]]:
    target = target_point_count(arm, prime)
    if target is None:
        raise ValueError("A_none has no local curve")
    attempts: list[dict] = []
    for attempt_number, (a, b) in enumerate(_curve_candidate_order(prime, seed, arm), 1):
        if max_attempts is not None and attempt_number > max_attempts:
            raise LocalConditionError(
                f"curve-search cap {max_attempts} reached for prime {prime}; no certificate"
            )
        curve = Curve(prime, a, b)
        core = discriminant_core(curve)
        attempt = {"attempt": attempt_number, "a": a, "b": b, "discriminant_core": core}
        if core == 0:
            attempt["rejection"] = "singular"
            attempts.append(attempt)
            continue
        points = curve_points(curve)
        attempt["point_count"] = len(points)
        if len(points) != target:
            attempt["rejection"] = "point_count"
            attempts.append(attempt)
            continue
        generator = cyclic_generator(curve, points)
        if generator is None:
            attempt["rejection"] = "noncyclic_group"
            attempts.append(attempt)
            continue
        attempt["accepted"] = True
        attempts.append(attempt)
        return curve, points, generator, attempts
    raise LocalConditionError(
        f"exhausted all short Weierstrass curves over F_{prime} without a certified target"
    )


def _point_json(point: Point) -> list[int] | None:
    return None if point is None else [point[0], point[1]]


def _point_from_json(value: list[int] | None) -> Point:
    return None if value is None else (int(value[0]), int(value[1]))


def _select_shared_scalars(
    curves: list[Curve],
    generators: list[Point],
    group_orders: list[int],
    r: int,
    seed: str,
    max_attempts: int,
) -> tuple[list[int], list[list[Point]], list[dict]]:
    if max_attempts < 1:
        raise LocalConditionError(
            f"shared-scalar search cap {max_attempts} reached; "
            "quotient compatibility not certified"
        )
    attempts: list[dict] = []
    rng = random.Random(_seed_int(seed, "shared-scalars", r, *group_orders))
    # Zero selects O, whose seven-column Weierstrass row is identically zero.
    base = list(range(1, r + 1))

    def candidate_vectors() -> Iterable[list[int]]:
        yield base
        produced = 1
        # A single bad local incidence minor is commonly repaired by moving
        # one label.  Try these sparse deterministic repairs before drawing
        # dense pseudorandom vectors; this also keeps retained rejection logs
        # small for the r=6 secondary arms.
        for delta in range(1, 1025):
            for point_index in range(r):
                if produced >= max_attempts:
                    return
                candidate = list(base)
                candidate[point_index] += delta
                yield candidate
                produced += 1
        while produced < max_attempts:
            yield [rng.randrange(0, 2**31) for _ in range(r)]
            produced += 1

    for attempt_number, scalars in enumerate(candidate_vectors(), 1):
        selected_by_prime: list[list[Point]] = []
        rejection = None
        rejection_prime = None
        rejection_rank = None
        for curve, generator, order in zip(curves, generators, group_orders):
            residues = [scalar % order for scalar in scalars]
            if 0 in residues:
                rejection = "point_at_infinity"
                rejection_prime = curve.p
                break
            if len(set(residues)) != r:
                rejection = "points_not_distinct"
                rejection_prime = curve.p
                break
            selected = [point_mul(curve, scalar, generator) for scalar in scalars]
            rank = matrix_rank_mod(
                (weierstrass_incidence_row(point, curve.p) for point in selected),
                curve.p,
            )
            if rank != r:
                rejection = "incidence_rank"
                rejection_prime = curve.p
                rejection_rank = rank
                break
            selected_by_prime.append(selected)
        record = {"attempt": attempt_number, "scalars": scalars}
        if rejection:
            record.update({"rejection": rejection, "prime": rejection_prime})
            if rejection_rank is not None:
                record["computed_rank"] = rejection_rank
            attempts.append(record)
            continue
        record["accepted"] = True
        attempts.append(record)
        return scalars, selected_by_prime, attempts
    raise LocalConditionError(
        f"shared-scalar search cap {max_attempts} reached; quotient compatibility not certified"
    )


def _make_incompatible_control(
    curves: list[Curve],
    generators: list[Point],
    group_orders: list[int],
    selected_by_prime: list[list[Point]],
    shared_scalars: list[int],
) -> tuple[list[list[Point]], list[list[int]], dict]:
    """Break the first common cyclic quotient while retaining local validity."""
    actual_points = [list(points) for points in selected_by_prime]
    actual_residues = [
        [scalar % order for scalar in shared_scalars] for order in group_orders
    ]
    first = next(
        (
            (
                left_index,
                right_index,
                math.gcd(group_orders[left_index], group_orders[right_index]),
            )
            for left_index, right_index in itertools.combinations(range(len(curves)), 2)
            if math.gcd(group_orders[left_index], group_orders[right_index]) > 1
        ),
        None,
    )
    if first is None:
        raise LocalConditionError(
            "I_incompatible requires a nontrivial common quotient; "
            "all admitted local orders are pairwise coprime"
        )
    left_index, right_index, common = first
    tau = _divisors(common)[0]
    left_images = [residue % tau for residue in actual_residues[left_index]]
    curve = curves[right_index]
    generator = generators[right_index]
    order = group_orders[right_index]
    attempts: list[dict] = []
    attempt_number = 0
    for point_index, original_residue in enumerate(actual_residues[right_index]):
        for delta in range(1, order):
            attempt_number += 1
            candidate_residue = (original_residue + delta) % order
            record = {
                "attempt": attempt_number,
                "point_index": point_index,
                "delta": delta,
                "candidate_residue": candidate_residue,
                "candidate_quotient_image": candidate_residue % tau,
            }
            if candidate_residue == 0:
                record["rejection"] = "point_at_infinity"
                attempts.append(record)
                continue
            candidate_residues = list(actual_residues[right_index])
            candidate_residues[point_index] = candidate_residue
            if len(set(candidate_residues)) != len(candidate_residues):
                record["rejection"] = "points_not_distinct"
                attempts.append(record)
                continue
            if candidate_residue % tau == shared_scalars[point_index] % tau:
                record["rejection"] = "quotient_image_unchanged"
                attempts.append(record)
                continue
            right_images = [residue % tau for residue in candidate_residues]
            isomorphism_units = _quotient_isomorphism_units(
                left_images, right_images, tau
            )
            record["quotient_isomorphism_units"] = isomorphism_units
            if isomorphism_units:
                record["rejection"] = "quotient_tuple_still_isomorphic"
                attempts.append(record)
                continue
            candidate_points = [
                point_mul(curve, residue, generator) for residue in candidate_residues
            ]
            rank = matrix_rank_mod(
                (weierstrass_incidence_row(point, curve.p) for point in candidate_points),
                curve.p,
            )
            if rank != len(shared_scalars):
                record["rejection"] = "incidence_rank"
                record["computed_rank"] = rank
                attempts.append(record)
                continue
            record["accepted"] = True
            attempts.append(record)
            actual_residues[right_index] = candidate_residues
            actual_points[right_index] = candidate_points
            certificate = {
                "status": "certified_mismatch",
                "first_nontrivial_common_quotient": True,
                "left_prime": curves[left_index].p,
                "right_prime": curves[right_index].p,
                "mutated_prime": curves[right_index].p,
                "left_group_order": group_orders[left_index],
                "right_group_order": group_orders[right_index],
                "common_order_gcd": common,
                "tau": tau,
                "point_index": point_index,
                "original_scalar_label": shared_scalars[point_index],
                "original_residue": original_residue,
                "mutated_residue": candidate_residue,
                "left_quotient_image": shared_scalars[point_index] % tau,
                "right_quotient_image": candidate_residue % tau,
                "mismatch": True,
                "quotient_isomorphism_units": [],
                "quotient_tuples_isomorphic": False,
                "local_checks_preserved": {
                    "point_affine": True,
                    "points_distinct": True,
                    "weierstrass_incidence_rank": rank,
                },
                "mutation_attempts": attempts,
            }
            return actual_points, actual_residues, certificate
    raise LocalConditionError(
        "I_incompatible could not break the first common quotient while "
        "preserving affine, distinct, full-incidence-rank local points"
    )


def _quotient_isomorphism_units(
    left_images: list[int], right_images: list[int], tau: int
) -> list[int]:
    """Units giving a label-preserving isomorphism of two cyclic quotients."""
    return [
        unit
        for unit in range(1, tau)
        if math.gcd(unit, tau) == 1
        and [(unit * image) % tau for image in left_images] == right_images
    ]


def _compatibility_records(local: list[dict], shared_scalars: list[int]) -> list[dict]:
    records = []
    for left, right in itertools.combinations(local, 2):
        common = math.gcd(left["point_count"], right["point_count"])
        divisors = _divisors(common)
        left_residues = left.get(
            "selected_scalar_residues",
            [scalar % left["point_count"] for scalar in shared_scalars],
        )
        right_residues = right.get(
            "selected_scalar_residues",
            [scalar % right["point_count"] for scalar in shared_scalars],
        )
        quotient_images = {}
        for divisor in divisors:
            left_images = [scalar % divisor for scalar in left_residues]
            right_images = [scalar % divisor for scalar in right_residues]
            isomorphism_units = _quotient_isomorphism_units(
                left_images, right_images, divisor
            )
            quotient_images[str(divisor)] = {
                "left": left_images,
                "right": right_images,
                "equal": left_images == right_images,
                "isomorphism_units": isomorphism_units,
                "isomorphic": bool(isomorphism_units),
            }
        records.append(
            {
                "left_prime": left["prime"],
                "right_prime": right["prime"],
                "common_order_gcd": common,
                "quotient_divisors": divisors,
                "shared_scalar_residues": {
                    str(divisor): [scalar % divisor for scalar in shared_scalars]
                    for divisor in divisors
                },
                "actual_quotient_images": quotient_images,
                "method": "cyclic_generator_shared_scalars",
                "certified": all(
                    record["isomorphic"] for record in quotient_images.values()
                ),
            }
        )
    return records


def build_local_conditions(
    arm: str,
    r: int,
    primes: Iterable[int] | None = None,
    *,
    seed: str = "xedni-rank-decay-local-v1",
    target_product: int | None = None,
    max_curve_attempts: int | None = None,
    max_scalar_attempts: int = 20_000,
) -> dict:
    if arm not in ARMS:
        raise ValueError(f"arm must be one of {ARMS}")
    if isinstance(r, bool) or not isinstance(r, int) or not 2 <= r <= 9:
        raise ValueError("r must be an integer in [2,9]")
    if r > MAX_EXECUTABLE_R:
        raise LocalConditionError(
            "r>=7 is blocked: the frozen protocol has no certified "
            "general-cubic-to-Jacobian point-map bridge"
        )
    if not isinstance(seed, str) or not seed:
        raise ValueError("seed must be a nonempty string")
    if max_curve_attempts is not None and (
        isinstance(max_curve_attempts, bool)
        or not isinstance(max_curve_attempts, int)
        or max_curve_attempts < 0
    ):
        raise ValueError("max_curve_attempts must be None or a nonnegative integer")
    if (
        isinstance(max_scalar_attempts, bool)
        or not isinstance(max_scalar_attempts, int)
        or max_scalar_attempts < 0
    ):
        raise ValueError("max_scalar_attempts must be a nonnegative integer")
    if arm == "A_none":
        if primes is not None or target_product is not None:
            raise ValueError("A_none cannot carry CRT primes or a target product")
        return {
            "schema": SCHEMA,
            "status": STATUS,
            "arm": arm,
            "r": r,
            "seed": seed,
            "incidence_model": INCIDENCE_MODEL,
            "selection_mode": "none",
            "prime_pool": list(primes_7_to_97()),
            "requested_primes": [],
            "prime_rejections": [],
            "accepted_primes": [],
            "M": 1,
            "primary_estimand_eligible": True,
            "local": [],
            "shared_scalars": [],
            "scalar_attempts": [],
            "compatibility": {
                "status": "vacuous",
                "method": "no_local_conditions",
                "general_noncyclic_support": False,
                "primary_estimand_eligible": True,
                "pairs": [],
            },
        }

    prefix = None
    if target_product is not None:
        if primes is not None:
            raise ValueError("provide primes or target_product, not both")
        prefix = prime_prefix_for_product(arm, r, target_product)
        requested = prefix["primes"]
        inherited_rejections = prefix["eligibility_rejections"]
        selection_mode = "target_product_prefix"
    else:
        selection_mode = "explicit" if primes is not None else "default_pool"
        requested = list(primes if primes is not None else primes_7_to_97())
        inherited_rejections = []

    eligibility = eligible_primes(arm, r, requested)
    accepted_primes = eligibility["accepted"]
    rejections = inherited_rejections + eligibility["rejected"]
    if not accepted_primes:
        raise LocalConditionError("no eligible local primes remain")

    curves = []
    point_lists = []
    generators = []
    local = []
    for prime in accepted_primes:
        curve, points, generator, attempts = _find_local_curve(
            prime, arm, seed, max_curve_attempts
        )
        curves.append(curve)
        point_lists.append(points)
        generators.append(generator)
        local.append(
            {
                "prime": prime,
                "requested_point_count": target_point_count(arm, prime),
                "point_count": len(points),
                "a": curve.a,
                "b": curve.b,
                "discriminant_core": discriminant_core(curve),
                "nonsingular": True,
                "cyclic": True,
                "generator": _point_json(generator),
                "generator_order": len(points),
                "curve_attempts": attempts,
            }
        )

    group_orders = [len(points) for points in point_lists]
    scalars, selected_by_prime, scalar_attempts = _select_shared_scalars(
        curves, generators, group_orders, r, seed, max_scalar_attempts
    )
    selected_scalar_residues = [
        [scalar % order for scalar in scalars] for order in group_orders
    ]
    incompatibility = None
    if arm == "I_incompatible":
        selected_by_prime, selected_scalar_residues, incompatibility = (
            _make_incompatible_control(
                curves,
                generators,
                group_orders,
                selected_by_prime,
                scalars,
            )
        )
    for entry, curve, selected, residues in zip(
        local, curves, selected_by_prime, selected_scalar_residues
    ):
        entry["selected_points"] = [_point_json(point) for point in selected]
        entry["selected_scalar_residues"] = residues
        entry["incidence_rank"] = matrix_rank_mod(
            (weierstrass_incidence_row(point, curve.p) for point in selected), curve.p
        )
        entry["incidence_model"] = INCIDENCE_MODEL
        entry["general_cubic_incidence_rank_diagnostic"] = matrix_rank_mod(
            (general_cubic_incidence_row(point, curve.p) for point in selected),
            curve.p,
        )
        entry["all_selected_points_affine"] = all(point is not None for point in selected)
        entry["weierstrass_coefficient_vector"] = [
            1,
            0,
            0,
            (-1) % curve.p,
            0,
            (-curve.a) % curve.p,
            (-curve.b) % curve.p,
        ]

    product = math.prod(accepted_primes)
    compatibility_pairs = _compatibility_records(local, scalars)
    if arm == "I_incompatible":
        compatibility = {
            "status": "deliberately_incompatible",
            "method": "cyclic_generator_shared_scalars_then_one_point_mutation",
            "general_noncyclic_support": False,
            "primary_estimand_eligible": False,
            "scope": "all divisors >1 of every pairwise gcd of local group orders",
            "incompatibility": incompatibility,
            "pairs": compatibility_pairs,
        }
    else:
        compatibility = {
            "status": "certified",
            "method": "cyclic_generator_shared_scalars",
            "general_noncyclic_support": False,
            "primary_estimand_eligible": True,
            "scope": "all divisors >1 of every pairwise gcd of local group orders",
            "pairs": compatibility_pairs,
        }
    result = {
        "schema": SCHEMA,
        "status": STATUS,
        "arm": arm,
        "r": r,
        "seed": seed,
        "incidence_model": INCIDENCE_MODEL,
        "selection_mode": selection_mode,
        "prime_pool": list(primes_7_to_97()),
        "requested_primes": requested,
        "prime_rejections": rejections,
        "accepted_primes": accepted_primes,
        "M": product,
        "target_product": target_product,
        "target_product_reached": target_product is None or product >= target_product,
        "primary_estimand_eligible": arm != "I_incompatible",
        "local": local,
        "shared_scalars": scalars,
        "scalar_attempts": scalar_attempts,
        "compatibility": compatibility,
    }
    errors = check_local_conditions(result)
    if errors:
        raise LocalConditionError("internal certificate check failed: " + "; ".join(errors))
    return result


def _strict_point_from_json(value: Any, prime: int, *, affine: bool) -> Point:
    if value is None:
        if affine:
            raise ValueError("point at infinity is not permitted")
        return None
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(
            isinstance(coordinate, bool) or not isinstance(coordinate, int)
            for coordinate in value
        )
    ):
        raise ValueError("point must be null or a two-integer JSON array")
    if any(coordinate < 0 or coordinate >= prime for coordinate in value):
        raise ValueError("point coordinate is not a canonical field residue")
    return value[0], value[1]


def _expected_prime_fields(config: dict, arm: str, r: int) -> tuple[list, list, list]:
    mode = config.get("selection_mode")
    if mode == "default_pool":
        if config.get("target_product") is not None:
            raise ValueError("default_pool cannot carry target_product")
        requested = list(primes_7_to_97())
        inherited_rejections: list[dict] = []
    elif mode == "explicit":
        if config.get("target_product") is not None:
            raise ValueError("explicit selection cannot carry target_product")
        requested = config.get("requested_primes")
        if not isinstance(requested, list):
            raise ValueError("requested_primes is not a list")
        inherited_rejections = []
    elif mode == "target_product_prefix":
        target = config.get("target_product")
        if isinstance(target, bool) or not isinstance(target, int) or target < 1:
            raise ValueError("invalid target_product")
        prefix = prime_prefix_for_product(arm, r, target)
        requested = prefix["primes"]
        inherited_rejections = prefix["eligibility_rejections"]
    else:
        raise ValueError("unknown selection_mode")
    eligibility = eligible_primes(arm, r, requested)
    return requested, eligibility["accepted"], inherited_rejections + eligibility["rejected"]


def _check_local_conditions(config: dict) -> list[str]:
    errors: list[str] = []
    if config.get("schema") != SCHEMA:
        errors.append("schema")
        return errors
    if config.get("status") != STATUS:
        errors.append("status")
    if config.get("incidence_model") != INCIDENCE_MODEL:
        errors.append("incidence_model")
    if config.get("prime_pool") != list(primes_7_to_97()):
        errors.append("prime_pool")

    arm = config.get("arm")
    r = config.get("r")
    seed = config.get("seed")
    if arm not in ARMS:
        errors.append("arm")
        return errors
    if isinstance(r, bool) or not isinstance(r, int) or not 2 <= r <= MAX_EXECUTABLE_R:
        errors.append("r_or_blocked_model")
        return errors
    if not isinstance(seed, str) or not seed:
        errors.append("seed")
        return errors
    local = config.get("local")
    if not isinstance(local, list):
        errors.append("local")
        return errors

    if arm == "A_none":
        expected_compatibility = {
            "status": "vacuous",
            "method": "no_local_conditions",
            "general_noncyclic_support": False,
            "primary_estimand_eligible": True,
            "pairs": [],
        }
        empty_fields = (
            config.get("selection_mode") == "none"
            and config.get("requested_primes") == []
            and config.get("prime_rejections") == []
            and config.get("accepted_primes") == []
            and local == []
            and config.get("shared_scalars") == []
            and config.get("scalar_attempts") == []
        )
        if not empty_fields or config.get("M") != 1:
            errors.append("A_none_not_empty")
        if config.get("primary_estimand_eligible") is not True:
            errors.append("primary_estimand_eligible")
        if config.get("compatibility") != expected_compatibility:
            errors.append("A_none_compatibility")
        return errors

    scalars = config.get("shared_scalars")
    if (
        not isinstance(scalars, list)
        or len(scalars) != r
        or any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in scalars
        )
    ):
        errors.append("shared_scalars")
        return errors

    requested, expected_accepted, expected_rejections = _expected_prime_fields(config, arm, r)
    if config.get("requested_primes") != requested:
        errors.append("requested_primes")
    if config.get("accepted_primes") != expected_accepted:
        errors.append("accepted_primes")
    if config.get("prime_rejections") != expected_rejections:
        errors.append("prime_rejections")
    if [entry.get("prime") for entry in local if isinstance(entry, dict)] != expected_accepted:
        errors.append("local_primes")
    if len(local) != len(expected_accepted):
        errors.append("local_length")
        return errors
    if config.get("M") != math.prod(expected_accepted):
        errors.append("M")
    if config.get("primary_estimand_eligible") is not (arm != "I_incompatible"):
        errors.append("primary_estimand_eligible")
    target_product = config.get("target_product")
    if target_product is not None:
        if config.get("M", 0) < target_product:
            errors.append("target_product")
        if config.get("target_product_reached") is not True:
            errors.append("target_product_reached")
    elif config.get("target_product_reached") is not True:
        errors.append("target_product_reached")

    curves: list[Curve] = []
    generators: list[Point] = []
    group_orders: list[int] = []
    expected_selected_by_prime: list[list[Point]] = []
    for entry, prime in zip(local, expected_accepted):
        if not isinstance(entry, dict):
            errors.append(f"local_entry:{prime}")
            continue
        a, b = entry.get("a"), entry.get("b")
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (a, b)):
            errors.append(f"curve_coefficients:{prime}")
            continue
        if not (0 <= a < prime and 0 <= b < prime):
            errors.append(f"curve_coefficients:{prime}")
            continue
        curve = Curve(prime, a, b)
        curves.append(curve)
        if not is_nonsingular(curve) or entry.get("discriminant_core") != discriminant_core(curve):
            errors.append(f"nonsingular:{prime}")
            continue
        if entry.get("nonsingular") is not True or entry.get("cyclic") is not True:
            errors.append(f"curve_flags:{prime}")
        points = curve_points(curve)
        expected_count = target_point_count(arm, prime)
        if (
            entry.get("requested_point_count") != expected_count
            or entry.get("point_count") != expected_count
            or len(points) != expected_count
        ):
            errors.append(f"point_count:{prime}")
        try:
            generator = _strict_point_from_json(entry.get("generator"), prime, affine=True)
        except ValueError:
            errors.append(f"generator_encoding:{prime}")
            continue
        generators.append(generator)
        group_orders.append(len(points))
        if (
            generator not in points
            or point_order(curve, generator, len(points)) != len(points)
            or entry.get("generator_order") != len(points)
        ):
            errors.append(f"generator:{prime}")

        attempts = entry.get("curve_attempts")
        if not isinstance(attempts, list) or not attempts:
            errors.append(f"curve_attempts:{prime}")
        else:
            try:
                (
                    expected_curve,
                    expected_points,
                    expected_generator,
                    expected_attempts,
                ) = _find_local_curve(prime, arm, seed, len(attempts))
                if (
                    expected_curve != curve
                    or len(expected_points) != len(points)
                    or expected_generator != generator
                    or expected_attempts != attempts
                ):
                    errors.append(f"curve_attempts:{prime}")
            except LocalConditionError:
                errors.append(f"curve_attempts:{prime}")

        raw_selected = entry.get("selected_points")
        if not isinstance(raw_selected, list):
            errors.append(f"selected_points:{prime}")
            continue
        try:
            selected = [
                _strict_point_from_json(value, prime, affine=True) for value in raw_selected
            ]
        except ValueError:
            errors.append(f"selected_points:{prime}")
            continue
        if len(selected) != r or len(set(selected)) != r:
            errors.append(f"distinct_points:{prime}")
            continue
        if any(not on_curve(curve, point) for point in selected):
            errors.append(f"points_on_curve:{prime}")
        residues = entry.get("selected_scalar_residues")
        if (
            not isinstance(residues, list)
            or len(residues) != r
            or any(
                isinstance(value, bool)
                or not isinstance(value, int)
                or value <= 0
                or value >= len(points)
                for value in residues
            )
            or len(set(residues)) != r
        ):
            errors.append(f"selected_scalar_residues:{prime}")
            continue
        base_residues = [scalar % len(points) for scalar in scalars]
        if arm != "I_incompatible" and residues != base_residues:
            errors.append(f"shared_scalar_residues:{prime}")
        expected_selected = [point_mul(curve, residue, generator) for residue in residues]
        expected_selected_by_prime.append(expected_selected)
        if selected != expected_selected:
            errors.append(f"shared_scalar_points:{prime}")
        rank = matrix_rank_mod(
            (weierstrass_incidence_row(point, prime) for point in selected), prime
        )
        if rank != r or entry.get("incidence_rank") != r:
            errors.append(f"incidence_rank:{prime}")
        diagnostic_rank = matrix_rank_mod(
            (general_cubic_incidence_row(point, prime) for point in selected), prime
        )
        if entry.get("general_cubic_incidence_rank_diagnostic") != diagnostic_rank:
            errors.append(f"general_cubic_diagnostic:{prime}")
        if entry.get("incidence_model") != INCIDENCE_MODEL:
            errors.append(f"incidence_model:{prime}")
        if entry.get("all_selected_points_affine") is not True:
            errors.append(f"affine_points:{prime}")
        coefficient_vector = [1, 0, 0, (-1) % prime, 0, (-a) % prime, (-b) % prime]
        if entry.get("weierstrass_coefficient_vector") != coefficient_vector:
            errors.append(f"coefficient_vector:{prime}")
        for point in selected:
            row = weierstrass_incidence_row(point, prime)
            if sum(left * right for left, right in zip(row, coefficient_vector)) % prime:
                errors.append(f"incidence_kernel:{prime}")
                break

    # Recompute the complete deterministic scalar search, including every
    # rejected vector.  This check is meaningful only after all local groups
    # supplied valid cyclic generators.
    scalar_attempts = config.get("scalar_attempts")
    recomputed_base_points: list[list[Point]] | None = None
    if len(curves) == len(local) and len(generators) == len(local):
        if not isinstance(scalar_attempts, list) or not scalar_attempts:
            errors.append("scalar_attempts")
        else:
            try:
                expected_scalars, expected_points, expected_attempts = _select_shared_scalars(
                    curves,
                    generators,
                    group_orders,
                    r,
                    seed,
                    len(scalar_attempts),
                )
                if expected_scalars != scalars or expected_attempts != scalar_attempts:
                    errors.append("scalar_attempts")
                recomputed_base_points = expected_points
                if arm != "I_incompatible" and expected_points != expected_selected_by_prime:
                    errors.append("scalar_selected_points")
            except LocalConditionError:
                errors.append("scalar_attempts")

    if arm == "I_incompatible":
        if recomputed_base_points is None:
            errors.append("incompatibility_base")
            expected_incompatibility = None
        else:
            try:
                expected_mutated_points, expected_residues, expected_incompatibility = (
                    _make_incompatible_control(
                        curves,
                        generators,
                        group_orders,
                        recomputed_base_points,
                        scalars,
                    )
                )
                actual_residues = [entry.get("selected_scalar_residues") for entry in local]
                actual_points = [
                    [
                        _strict_point_from_json(value, entry["prime"], affine=True)
                        for value in entry.get("selected_points", [])
                    ]
                    for entry in local
                ]
                if (
                    actual_residues != expected_residues
                    or actual_points != expected_mutated_points
                ):
                    errors.append("incompatibility_mutation")
            except (LocalConditionError, ValueError):
                errors.append("incompatibility_mutation")
                expected_incompatibility = None
        expected_compatibility = {
            "status": "deliberately_incompatible",
            "method": "cyclic_generator_shared_scalars_then_one_point_mutation",
            "general_noncyclic_support": False,
            "primary_estimand_eligible": False,
            "scope": "all divisors >1 of every pairwise gcd of local group orders",
            "incompatibility": expected_incompatibility,
            "pairs": _compatibility_records(local, scalars),
        }
        if not any(not pair["certified"] for pair in expected_compatibility["pairs"]):
            errors.append("incompatibility_missing")
    else:
        expected_compatibility = {
            "status": "certified",
            "method": "cyclic_generator_shared_scalars",
            "general_noncyclic_support": False,
            "primary_estimand_eligible": True,
            "scope": "all divisors >1 of every pairwise gcd of local group orders",
            "pairs": _compatibility_records(local, scalars),
        }
    compatibility = config.get("compatibility")
    expected_status = (
        "deliberately_incompatible" if arm == "I_incompatible" else "certified"
    )
    if not isinstance(compatibility, dict) or compatibility.get("status") != expected_status:
        errors.append("compatibility_status")
    elif compatibility != expected_compatibility:
        errors.append("compatibility_pairs")
    return errors


def check_local_conditions(config: Any) -> list[str]:
    """Recompute a certificate and fail closed on every malformed input."""
    if not isinstance(config, dict):
        return ["config"]
    try:
        return _check_local_conditions(config)
    except (ArithmeticError, IndexError, KeyError, TypeError, ValueError) as error:
        return [f"malformed:{type(error).__name__}"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--arm", choices=ARMS, required=True)
    build.add_argument("--r", type=int, required=True)
    build.add_argument("--primes", help="comma-separated primes in the inclusive 7..97 pool")
    build.add_argument("--target-product", type=int)
    build.add_argument("--seed", default="xedni-rank-decay-local-v1")
    build.add_argument("--max-curve-attempts", type=int)
    build.add_argument("--max-scalar-attempts", type=int, default=20_000)
    build.add_argument("--output", type=Path)
    check = subparsers.add_parser("check")
    check.add_argument("input", type=Path)
    args = parser.parse_args()

    if args.command == "build":
        primes = None if args.primes is None else [int(value) for value in args.primes.split(",")]
        result = build_local_conditions(
            args.arm,
            args.r,
            primes,
            seed=args.seed,
            target_product=args.target_product,
            max_curve_attempts=args.max_curve_attempts,
            max_scalar_attempts=args.max_scalar_attempts,
        )
        rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered)
        print(rendered, end="")
        return

    config = json.loads(args.input.read_text())
    errors = check_local_conditions(config)
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
