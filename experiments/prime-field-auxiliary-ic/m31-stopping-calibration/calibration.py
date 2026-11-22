"""Query quantiles under independent uniform draws and collision-free signed pairs."""
from decimal import Decimal, getcontext
from functools import cache
import json
from math import comb, factorial
from pathlib import Path

getcontext().prec = 96
GROUP_ORDER = 2147505293


@cache
def components(size):
    trees = 1 if size == 1 else 2**(size-1) * size**(size-2)
    unicyclic = size * trees
    for length in range(2, size + 1):
        cycles = 1 if length == 2 else factorial(length-1) * 2**(length-2)
        extra = size - length
        forests = length * size**(extra-1) * 2**extra if extra else 1
        unicyclic += comb(size, length) * cycles * forests
    return trees, unicyclic


@cache
def independent(vertices, rows):
    if not 0 <= rows <= vertices:
        return 0
    if vertices == 0:
        return 1
    count = 0
    for size in range(1, vertices + 1):
        trees, unicyclic = components(size)
        rest = vertices - size
        count += comb(vertices-1, size-1) * (
            trees * independent(rest, rows-size+1) + unicyclic * independent(rest, rows-size))
    return count


def occupancy(k, queries):
    """Probabilities of 0 through k distinct classes after the given query count."""
    classes = k*k
    powers = [(1 - Decimal(2*(classes-i))/GROUP_ORDER)**queries for i in range(k+1)]
    return [comb(classes, r) * sum((-1)**(r-i) * comb(r, i) * powers[i] for i in range(r+1))
            for r in range(k+1)]


def cdf(k, queries):
    survival = sum(prob * independent(k, r) / comb(k*k, r)
                   for r, prob in enumerate(occupancy(k, queries)))
    return 1 - survival


def quantile(k, probability):
    low, high = 0, 200000000
    assert cdf(k, high) >= probability
    while high - low > 1:
        middle = (low + high) // 2
        if cdf(k, middle) >= probability:
            high = middle
        else:
            low = middle
    return high


for k in (17, 20):
    levels = map(Decimal, ('.05', '.25', '.50', '.75', '.95'))
    print('quantiles', k, [quantile(k, level) for level in levels])

folder = Path(__file__).resolve().parent.parent / "snapshot/algebraic/optimized/results/field31_s5_base0"
for seed in range(3):
    data = json.loads((folder / f"v2_batch_seed{seed}.audited.json").read_text())
    q, r = data["queries"], data["relations"]
    print(seed, q, r, float(cdf(17, q)), float(1 - sum(occupancy(17, q)[:r])))
