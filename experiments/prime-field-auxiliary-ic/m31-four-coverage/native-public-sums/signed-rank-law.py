"""Fixed-deadline rank probabilities for the archived 17-coordinate iid reference.

There are 289 equally likely signed row classes modulo overall sign, each with
two disjoint endpoints in a group of order Q. Repeated classes are discarded.
The event is linear dependence of distinct rows, over an odd-characteristic
field. It is evaluated without any final extraction or verification assumption.
"""
from collections import Counter
from decimal import Decimal
from fractions import Fraction
from math import comb, factorial
from pathlib import Path
import runpy

occupancy = runpy.run_path(str(Path(__file__).resolve().parents[1] / "archive-occupancy.py"))
Q, SCALE = occupancy["Q"], occupancy["SCALE"]
power_bounds = occupancy["probability_power"]


def independent_subsets(k):
    """Component decomposition from m31-signed-graph-counts/Counts.lean."""
    rows = [[1]]
    for n in range(1, k + 1):
        row = [0] * (n + 1)
        for j in range(1, n + 1):
            tree = 2**(j-1) * j**max(0, j-2)
            cycle = j * tree
            for length in range(2, j + 1):
                core = 1 if length == 2 else factorial(length-1) * 2**(length-2)
                attach = 1 if length == j else length * (2*j)**(j-length) // j
                cycle += comb(j, length) * core * attach
            choices = comb(n-1, j-1)
            for r, smaller in enumerate(rows[n-j]):
                row[r+j-1] += choices * tree * smaller
                row[r+j] += choices * cycle * smaller
        rows.append(row)
    return rows[-1]


def check_ordered_counts(k, counts):
    # A positive size represents a tree; a negative size represents a
    # connected component containing one unbalanced cycle.
    states = {(1,) * k: 1}
    for r, count in enumerate(counts):
        assert sum(states.values()) == count * factorial(r)
        following = Counter()
        for state, weight in states.items():
            for i, u in enumerate(state):
                if u > 0:
                    # One loop per vertex, or the unbalanced sign for a pair.
                    closed = state[:i] + state[i+1:] + (-u,)
                    following[tuple(sorted(closed))] += weight * (u*(u+1)//2)
                for j in range(i+1, len(state)):
                    v = state[j]
                    if u < 0 and v < 0:
                        continue
                    size = abs(u) + abs(v)
                    merged = size if u > 0 and v > 0 else -size
                    joined = state[:i] + state[i+1:j] + state[j+1:] + (merged,)
                    following[tuple(sorted(joined))] += weight * 2 * abs(u*v)
        states = following


def family_mass(k, draws, subset_counts):
    # For one specified r-subset, inclusion-exclusion forces every label in
    # it to appear, while excluding draws from the other k²-r labels.
    coefficients = Counter()
    for r, count in enumerate(subset_counts):
        for j in range(r + 1):
            coefficients[j] += count * (-1)**(r-j) * comb(r, j)
    lo = hi = 0
    for j, coefficient in coefficients.items():
        left, right = power_bounds(Q-2*(k*k-j), Q, draws)
        if coefficient < 0:
            left, right = right, left
        lo += coefficient * left
        hi += coefficient * right
    return lo, hi


def by_deadline(k, draws):
    lo, hi = family_mass(k, draws, independent_subsets(k))
    return SCALE-hi, SCALE-lo


if __name__ == "__main__":
    assert independent_subsets(5) == [1, 25, 300, 2220, 10410, 25218]
    counts = independent_subsets(17)
    check_ordered_counts(17, counts)
    # Compare with the published companion study's rounded waiting-time mean.
    mean = sum(Fraction(c * Q, comb(289, r)*2*(289-r)) for r, c in enumerate(counts))
    assert 48_700_441 < mean < 48_700_443
    dependent_triples = comb(289, 3) - counts[3]
    assert dependent_triples == 4*(comb(17, 2) + comb(17, 3)) == 3264
    print("draws   P(dependency)   share with exactly three distinct labels")
    for budget in [25_484, 81_795, 71_462, 18_999_999, 34_771_537, 19_300_166, 45_496_514]:
        lo, hi = by_deadline(17, budget)
        assert 0 < lo <= hi <= SCALE and (hi-lo)*10**15 < lo
        triples_lo, triples_hi = family_mass(17, budget, [0, 0, 0, dependent_triples])
        share_lo, share_hi = Fraction(triples_lo, hi), Fraction(triples_hi, lo)
        assert 0 < share_lo <= share_hi < 1 and share_hi-share_lo < Fraction(1, 10**12)
        print(budget, f"{Decimal(lo+hi) / Decimal(2*SCALE):.12g}",
              f"{100*float((share_lo+share_hi)/2):.6f}%")
