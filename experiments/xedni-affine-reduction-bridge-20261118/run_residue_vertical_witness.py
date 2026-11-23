"""Replay the exact residue-vertical chord witness with rational arithmetic."""

from fractions import Fraction
import json
from pathlib import Path


P = 5
A = -5
B = -8
FIRST = (4, 6)
SECOND = (9, -26)


def valuation(value: Fraction, prime: int) -> int:
    def exponent(n: int) -> int:
        result = 0
        while n % prime == 0:
            n //= prime
            result += 1
        return result

    assert value != 0
    return exponent(abs(value.numerator)) - exponent(value.denominator)


def on_curve(point: tuple[int | Fraction, int | Fraction]) -> bool:
    x, y = point
    return y * y == x * x * x + A * x + B


def main() -> None:
    x1, y1 = FIRST
    x2, y2 = SECOND
    assert on_curve(FIRST) and on_curve(SECOND)
    assert (x1 - x2) % P == 0 and (y1 + y2) % P == 0
    assert (y2 - y1) % P != 0
    discriminant = -16 * (4 * A**3 + 27 * B**2)
    assert discriminant % P != 0

    slope = Fraction(y2 - y1, x2 - x1)
    x3 = slope * slope - x1 - x2
    y3 = slope * (x1 - x3) - y1
    assert on_curve((x3, y3))
    assert slope == Fraction(-32, 5)
    assert x3 == Fraction(699, 25)
    assert y3 == Fraction(18418, 125)

    result = {
        "field_prime": P,
        "curve": {"a": A, "b": B, "discriminant_mod_p": discriminant % P},
        "points": {"first": list(FIRST), "second": list(SECOND)},
        "residue_points": {
            "first": [x1 % P, y1 % P],
            "second": [x2 % P, y2 % P],
            "sum": "infinity",
        },
        "chord": {
            "slope": [slope.numerator, slope.denominator],
            "sum_x": [x3.numerator, x3.denominator],
            "sum_y": [y3.numerator, y3.denominator],
            "v_p_x": valuation(x3, P),
            "v_p_y": valuation(y3, P),
        },
        "checks": {
            "input_points_on_curve": True,
            "rational_sum_on_curve": True,
            "smooth_reduction": True,
            "residue_inverse": True,
            "nonzero_reduced_chord_numerator": True,
        },
    }
    output = Path(__file__).with_name("residue-vertical-witness-result.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
