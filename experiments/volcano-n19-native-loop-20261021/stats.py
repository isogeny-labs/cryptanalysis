"""The frozen statistics of volcano-n19-native-loop-20261021 (protocol.json "statistics"), standard library only.

Shared by power_check.py and verify_receipt.py. The data of one comparison is
`points`: one list per panel point of (a, b) pairs, a and b being the two
processes of one alternating pair (N and N2, N2 and N2aa, or N2X and N2).

* ratio_of_sums: sum a / sum b over every pair of every point (the primary).
* two_stage: paired two-stage bootstrap, as the n = 83 replication's
  verifier: draw the points with replacement, then within each drawn point
  draw its pairs with replacement (a and b of a pair stay together);
  DRAWS draws from random.Random(seed); the 95% interval is the 2.5% and
  97.5% order statistics.
"""
import math
import random
import statistics

DRAWS = 10000
SEED = 2026102101  # new (v3: 2026102003)


def ratio_of_sums(points):
    return sum(a for pairs in points for a, _ in pairs) / sum(b for pairs in points for _, b in pairs)


def geo_mean(points):
    return math.exp(statistics.mean(math.log(a / b) for pairs in points for a, b in pairs))


def two_stage(points, statistic=ratio_of_sums, seed=SEED, draws=DRAWS):
    points = [list(p) for p in points if p]
    if not points:
        return None
    rng = random.Random(seed)
    n = len(points)
    values = []
    for _ in range(draws):
        sample = []
        for _ in range(n):
            pairs = points[rng.randrange(n)]
            sample.append([pairs[rng.randrange(len(pairs))] for _ in pairs])
        values.append(statistic(sample))
    values.sort()
    return {'estimate': statistic(points), 'ci95': [values[int(0.025 * draws)], values[int(0.975 * draws) - 1]],
            'n_points': n, 'n_pairs': sum(len(p) for p in points), 'draws': draws, 'seed': seed,
            'bootstrap': 'two-stage paired: points, then pairs within each drawn point'}


def verdict(lo, hi):
    if lo > 1:
        return 'improvement'
    if hi < 1:
        return 'regression'
    return 'not_separated'
