#!/usr/bin/env python3
"""Integer certificate for the bounded aggregate ray-character screen."""

from math import isqrt

P = 6277101735386680763835789423207666416083908700390324961279
R = 6277101735386680763835789423176059013767194773182842284081


def main():
    # At most 100 factors, each pulled back through degree <=100 and
    # having rational-function degree <=100 on its endpoint curve.
    dmax = 100 * 100 * 100
    root_upper = isqrt(P) + 1
    # Replacing sqrt(p) by its integer upper bound weakens the theorem's
    # right-hand side. The quotient's ceiling still gives the stated floor.
    numerator = P - 1 - 2 * root_upper
    exact_floor = (numerator + 20 * root_upper - 1) // (20 * root_upper)
    assert exact_floor == 3961408125713216879677197517
    assert dmax == 1_000_000 < exact_floor

    # Apply equation (8) of OUTER_CHARACTER_DEGREE_GATE.md with a strict
    # upper bound sqrt(p)<2^96. The reported agreement bound is uniform
    # over every fixed product satisfying the regularity assumptions.
    h = 1 << 24
    n = R - 1
    m_upper = (4 * h * h * dmax + 4) * (1 << 96) + 1
    assert P < (1 << 192) and h < min(P, R)
    assert 3600**2 * (n + (h - 1) * m_upper) < h * n
    print("PASS: degree <= 1000000 is below the exact-character floor")
    print("PASS: best full-group agreement < 1/2 + 1/7200")


if __name__ == "__main__":
    main()
