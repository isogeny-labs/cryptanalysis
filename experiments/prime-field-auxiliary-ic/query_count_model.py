"""Query-count reference model for independent uniform M31 points.

Given k distinct keys and survival, the independent k-element subsets are
equiprobable. For I[k] such subsets, double counting subset extensions gives
(k+1)*I[k+1] / I[k] surviving extensions on average. Repeated keys and
points outside the accepted set leave the retained subset unchanged.
The last matrix state absorbs the first linear dependency.
"""
import json
from math import comb
from pathlib import Path
import re

from signed_row_model import transitions

N = 2147505293
J = 289
TRACES = Path(__file__).resolve().parent / "snapshot/algebraic/optimized/results/field31_s5_base0"


def enclosure(counts, trials, precision=10**28):
    """Bound the absorbing probability with integer matrix products."""
    width = len(counts) + 1
    numerator = [[0] * width for _ in range(width)]
    denominator = []
    for i, count in enumerate(counts):
        extensions = (i + 1) * counts[i + 1] if i + 1 < len(counts) else 0
        den = N * count
        denominator.append(den)
        numerator[i][i] = (N - 2*(J-i)) * count
        if extensions:
            numerator[i][i+1] = 2 * extensions
        numerator[i][-1] = 2 * ((J-i)*count - extensions)
        assert min(numerator[i]) >= 0 and sum(numerator[i]) == den
    denominator.append(1)
    numerator[-1][-1] = 1

    def endpoint(upper):
        def scale(x, den):
            return (x + (den-1 if upper else 0)) // den
        power = [[scale(precision*x, den) for x in row]
                 for row, den in zip(numerator, denominator)]
        vector = [[precision] + [0]*(width-1)]
        def product(left, right):
            columns = list(zip(*right))
            return [[scale(sum(a*b for a,b in zip(row,col)), precision)
                     for col in columns] for row in left]
        t = trials
        while t:
            if t & 1:
                vector = product(vector, power)
            t >>= 1
            if t:
                power = product(power, power)
        return vector[0][-1]
    return endpoint(False), endpoint(True), precision

def quantile(counts, percent):
    def reached(t):
        low, high, scale = enclosure(counts, t)
        if 100 * low >= percent * scale:
            return True
        if 100 * high < percent * scale:
            return False
        raise ArithmeticError("increase interval precision")
    lo, hi = 0, 1
    while not reached(hi):
        hi *= 2
    while hi - lo > 1:
        middle = (lo + hi) // 2
        if reached(middle):
            hi = middle
        else:
            lo = middle
    return hi


def main():
    counts = transitions(17)
    for percent in (5, 50, 95):
        print("quantile", percent, quantile(counts, percent))
    for arm in ("v2_batch", "v2_chain"):
        for seed in range(3):
            stem = f"{arm}_seed{seed}"
            receipt = json.loads((TRACES / f"{stem}.audited.json").read_bytes())
            end = receipt["queries"]
            low, high, scale = enclosure(counts, end)
            print(stem, "first dependency CDF", low / scale, high / scale)
            log = (TRACES / f"{stem}.log").read_text()
            matches = re.findall(r"^queries 19000000, relations ([0-9]+),", log, re.MULTILINE)
            if len(matches) != 1:
                raise ValueError(f"{stem}: missing or ambiguous 19-million-query checkpoint")
            rows = int(matches[0])
            # Here all subsets of size below rows survive. Absorption occurs
            # as soon as the specified number of distinct keys has appeared.
            low, high, scale = enclosure([comb(J,k) for k in range(rows)], 19000000)
            print(stem, "prefix rows and upper tail", rows, low / scale, high / scale)


if __name__ == "__main__":
    main()
