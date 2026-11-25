"""Fixed-deadline and mean waiting times for uniform independent group queries."""
from collections import Counter
from fractions import Fraction
from math import comb
from pathlib import Path
import runpy

law = runpy.run_path(str(Path(__file__).with_name("signed-rank-law.py")))
Q = law["Q"]
SCALE = 10**170


def power_interval(numerator, exponent):
    def product(a, b):
        return a[0]*b[0]//SCALE, -(-a[1]*b[1]//SCALE)

    base = numerator*SCALE//Q, -(-numerator*SCALE//Q)
    result = SCALE, SCALE
    while exponent:
        if exponent & 1:
            result = product(result, base)
        base = product(base, base)
        exponent >>= 1
    return result


def summarize(labels, counts):
    # Given r distinct labels, all r-subsets are equally likely. An independent
    # prefix incurs the geometric wait for another distinct label.
    expectation = sum(Fraction(n*Q, comb(labels, r)*2*(labels-r))
                      for r, n in enumerate(counts))
    coeff = Counter()
    for r, n in enumerate(counts):
        for j in range(r+1):
            coeff[j] += n * (-1)**(r-j) * comb(r, j)

    def deadline(draws):
        lo = hi = 0
        for j, c in coeff.items():
            a, b = power_interval(Q - 2*(labels-j), draws)
            if c < 0:
                a, b = b, a
            lo += c*a
            hi += c*b
        return Fraction(SCALE-hi, SCALE), Fraction(SCALE-lo, SCALE)

    return expectation, deadline


def main():
    single = law["independent_subsets"](17)
    mixed = law["independent_subsets"](34)
    pooled = [0]*(2*len(single)-1)
    for i, a in enumerate(single):
        for j, b in enumerate(single):
            pooled[i+j] += a*b
    assert comb(1156, 3)-mixed[3] == 4*(comb(34, 2)+comb(34, 3))
    for name, labels, counts in (("single", 289, single), ("pooled", 578, pooled),
                                 ("mixed", 1156, mixed)):
        mean, deadline = summarize(labels, counts)
        print(name, "mean", float(mean))
        for budget in (25484, 81795, 71462):
            lo, hi = deadline(budget)
            assert 0 < lo <= hi < 1 and hi-lo < lo/10**15
            print(budget, f"{float((lo+hi)/2):.12g}")

        left, right = 0, 100_000_000
        while right - left > 1:
            mid = (left + right)//2
            lower, upper = deadline(mid)
            if lower >= Fraction(1, 2):
                right = mid
            else:
                assert upper < Fraction(1, 2)
                left = mid
        assert deadline(left)[1] < Fraction(1, 2) <= deadline(right)[0]
        print("median queries", right)


if __name__ == "__main__":
    main()
