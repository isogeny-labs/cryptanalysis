"""Discover M31 products from smooth representatives and replay from divisors."""
from collections import Counter, defaultdict
import json
import sys

P = 2**31 - 1
PRIMES = (3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
          53, 59, 61, 67, 71, 73, 79, 83)
BOUNDS = (47, 67, 71, 73, 79, 83)


def least_rotation(x):
    return min(((x << j) & P) | (x >> (31-j)) for j in range(31))


def canonical_pair(x, y):
    return tuple(sorted((least_rotation(x), least_rotation(y))))


def divisor_pairs(product, bound):
    residue = product % P
    assert residue and residue & (residue - 1) == 0
    remaining = product
    divisors = [1]
    for q in PRIMES:
        if q > bound:
            break
        old = divisors.copy()
        while remaining % q == 0:
            remaining //= q
            old = [d*q for d in old]
            divisors.extend(old)
    assert remaining == 1
    pairs = set()
    for d in divisors:
        e = product // d
        if d <= e < P and pow(d, (P-1)//2, P) == P-1:
            pair = canonical_pair(d, e)
            if pair[0] != pair[1]:
                pairs.add(pair)
    return pairs


def summarize(support):
    frequencies = Counter(pair for pairs in support.values() for pair in pairs)
    return dict(pairs=len(frequencies), multiple=sum(n > 1 for n in frequencies.values()),
                products={str(n): len(support[n]) for n in sorted(support)})


def discover():
    values = [1]
    report = {}
    for q in PRIMES:
        extra = []
        for v in values:
            v *= q
            while v < P:
                extra.append(v)
                v *= q
        values.extend(extra)
        if q not in BOUNDS:
            continue
        groups = defaultdict(list)
        for x in values:
            if pow(x, (P-1)//2, P) == P-1:
                groups[pow(x, 31, P)].append(x)
        support = defaultdict(set)
        for k, xs in groups.items():
            inv = pow(k, -1, P)
            if inv > k and inv in groups:
                for x in xs:
                    for y in groups[inv]:
                        support[x*y].add(canonical_pair(x,y))
        for n, pairs in support.items():
            assert pairs == divisor_pairs(n,q)
        report[str(q)] = summarize(support)
    return report


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print(json.dumps(discover(), indent=2))
    elif len(sys.argv) == 3 and sys.argv[1] == 'replay':
        with open(sys.argv[2]) as f:
            report = json.load(f)
        assert list(map(int, report)) == list(BOUNDS)
        for bound, row in report.items():
            assert row == summarize({int(n): divisor_pairs(int(n), int(bound))
                                     for n in row['products']})
        print('Replayed all six product lists.')
    else:
        sys.exit('usage: python3 census.py [replay report.json]')
