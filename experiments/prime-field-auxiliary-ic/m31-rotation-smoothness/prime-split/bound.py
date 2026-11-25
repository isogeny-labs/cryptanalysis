"""Candidate lower bounds for an unpruned two-list smooth-product search."""
from bisect import bisect_right
from functools import lru_cache
from itertools import combinations
from math import prod
import numpy as np

P = 2**31 - 1
Q = (2**31 - 2)**2
PRIMES = (3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83)


def positive_powers(primes, limit):
    """Products with every listed prime occurring at least once."""
    values = [1]
    for q in primes:
        extra = []
        for x in values:
            x *= q
            while x <= limit:
                extra.append(x)
                x *= q
        values = extra
    return sorted(values)


@lru_cache(None)
def count_support(primes):
    if not primes:
        return 1
    # Place the smaller primes on the bisected side.
    cut = (len(primes) + 1)//2
    left, right = primes[:cut], primes[cut:]
    xs = positive_powers(left, Q//prod(right))
    ys = positive_powers(right, Q//prod(left))
    return sum(bisect_right(xs, Q//y) for y in ys)


def representatives(primes):
    values = [1]
    for q in primes:
        extra = []
        for v in values:
            v *= q
            while v < P:
                extra.append(v)
                v *= q
        values.extend(extra)
    return len(values)


def audit(bound, depth):
    primes = tuple(q for q in PRIMES if q <= bound)
    weights = np.zeros(1 << len(primes), dtype=np.int64)
    for n in range(depth + 1):
        for indices in combinations(range(len(primes)), n):
            weights[sum(1 << i for i in indices)] = count_support(tuple(primes[i] for i in indices))
    for i in range(len(primes)):
        h = 1 << i
        blocks = weights.reshape(-1, 2*h)
        blocks[:, h:] += blocks[:, :h]
    costs = weights + weights[::-1]
    mask = int(costs.argmin())
    baseline = representatives(primes)
    return (bound,depth,len(primes),baseline,int(costs[mask]),mask)


if __name__ == '__main__':
    print('bound,maximum_support,prime_count,representatives,min_partial_list_entries,first_minimizing_mask')
    for bound in (47,67,83):
        for depth in (3,4,5):
            row = audit(bound,depth)
            print(*row, sep=',', flush=True)
            if row[4] > row[3]:
                break
