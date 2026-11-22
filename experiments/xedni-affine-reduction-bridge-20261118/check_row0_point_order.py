#!/usr/bin/env python3
"""Exact finite-field replay for the recorded row-0 public base point.

This standard-library check supplies a computational certificate for the
field-group and point orders. The corresponding Lean point-order proof is
tracked separately in RecordedPointOrder.lean.
"""

import argparse
import json
from pathlib import Path

FIELD_PRIME = 313
A = -1
B = 15961
BASE = (306, 125)
RECORDED_FOUR_BASE = (1, 183)
RESULT = Path(__file__).with_name("row0-point-order-result.json")


def add(left, right):
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    if x1 == x2 and (y1 + y2) % FIELD_PRIME == 0:
        return None
    if x1 == x2:
        denominator = (2 * y1) % FIELD_PRIME
        numerator = (3 * x1 * x1 + A) % FIELD_PRIME
    else:
        denominator = (x2 - x1) % FIELD_PRIME
        numerator = (y2 - y1) % FIELD_PRIME
    assert denominator != 0
    slope = numerator * pow(denominator, -1, FIELD_PRIME) % FIELD_PRIME
    x3 = (slope * slope - x1 - x2) % FIELD_PRIME
    y3 = (slope * (x1 - x3) - y1) % FIELD_PRIME
    assert (y3 * y3 - x3**3 - A * x3 - B) % FIELD_PRIME == 0
    return x3, y3


def run():
    p = FIELD_PRIME
    assert all(p % d for d in range(2, int(p**0.5) + 1))
    assert (BASE[1] ** 2 - BASE[0] ** 3 - A * BASE[0] - B) % p == 0

    # Count affine points by two independent exact methods.
    squares = [0] * p
    for y in range(p):
        squares[y * y % p] += 1
    count_by_squares = 1 + sum(squares[(x**3 + A * x + B) % p] for x in range(p))
    count_by_character = 1
    for x in range(p):
        rhs = (x**3 + A * x + B) % p
        count_by_character += 1 if rhs == 0 else 2 if pow(rhs, (p - 1) // 2, p) == 1 else 0
    assert count_by_squares == count_by_character

    multiples = []
    current = None
    for k in range(1, count_by_squares + 1):
        current = add(current, BASE)
        if k in (1, 2, 4, 8, 64, 256, 320, 328, 330, 331):
            multiples.append({"k": k, "point": list(current) if current is not None else None})
        if current is None:
            order = k
            break
    else:
        raise AssertionError("base point order exceeds curve point count")

    assert all(order % d for d in range(2, int(order**0.5) + 1))
    assert add(add(BASE, BASE), add(BASE, BASE)) == RECORDED_FOUR_BASE
    assert order == count_by_squares == 331
    return {
        "status": "exact_computational_check",
        "field_prime": p,
        "curve": {"model": "short_weierstrass", "a": A, "b": B},
        "base_point": list(BASE),
        "recorded_four_base": list(RECORDED_FOUR_BASE),
        "curve_order_by_squares": count_by_squares,
        "curve_order_by_character": count_by_character,
        "base_point_order": order,
        "cofactor": count_by_squares // order,
        "selected_multiples": multiples,
        "method": "exhaustive_x_count_and_repeated_affine_addition",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    computed = run()
    if args.check:
        assert json.loads(RESULT.read_text()) == computed
    else:
        RESULT.write_text(json.dumps(computed, indent=2, sort_keys=True) + "\n")
    print(json.dumps(computed, sort_keys=True))


if __name__ == "__main__":
    main()
