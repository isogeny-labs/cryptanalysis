"""Reproduce the matched public-coordinate incidence census using Python 3.8+."""
import csv
import hashlib
import itertools
import math
import random
import sys
from collections import Counter, defaultdict

P = 2**31 - 1
PRIMES = [q for q in range(2, 212) if all(q % d for d in range(2, math.isqrt(q) + 1))]


def smooth(n):
    for q in PRIMES:
        while n % q == 0:
            n //= q
    return n == 1


def paired(seed, require_smooth):
    rng = random.Random(202611254000 + 2 * seed + require_smooth)
    signs = random.Random(202611255000 + 2 * seed + require_smooth)
    arms = [[], [], []]
    used = set()
    for bits in range(21, 31):
        quota = len(used) + 50
        while len(used) < quota:
            u = rng.randrange(1 << (bits - 1), 1 << bits)
            if u in used or (require_smooth and not smooth(u)):
                continue
            points = []
            for x in (u, P-u):
                rhs = (x**3 + 2*x + 14) % P
                y = pow(rhs, (P+1)//4, P)
                if y*y % P != rhs:
                    break
                points.append((x, min(y, P-y)))
            if len(points) != 2:
                continue
            char = pow((u**3 + u) % P, (P-1)//2, P)
            assert char in (1, P-1)
            aux, twist = points if char == 1 else points[::-1]
            for arm, point in zip(arms, (aux, twist, points[signs.randrange(2)])):
                arm.append(point)
            used.add(u)
    return arms


def census(points):
    # Orient each signed pair sum to its even ordinate before comparing witnesses.
    by_x = defaultdict(list)
    for j, (b, v) in enumerate(points):
        for i, (a, u) in enumerate(points[:j]):
            inverse = pow(b-a, -1, P)
            for sign in (1, -1):
                slope = ((sign*v-u)*inverse) % P
                x = (slope*slope-a-b) % P
                y = (slope*(a-x)-u) % P
                orientation = -1 if y % 2 else 1
                by_x[x].append((i, j, orientation, orientation*sign))
    occurrences = Counter()
    for pairs in by_x.values():
        for (i,j,a,b), (k,l,c,d) in itertools.combinations(pairs, 2):
            if len({i,j,k,l}) != 4:
                continue
            row = sorted(((i,a), (j,b), (k,-c), (l,-d)))
            occurrences[tuple((col, val*row[0][1]) for col,val in row)] += 1
    if any(n != 3 for n in occurrences.values()):
        raise ValueError("Signed four-term row did not occur in three pairings")
    degree = Counter(col for row in occurrences for col,_ in row)
    private = sum(any(degree[col] == 1 for col,_ in row) for row in occurrences)
    return len(occurrences), private


def main():
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["panel","seed","smooth","orientation","rows","rows_with_private_column","magnitude_sha256"])
    for seed in range(36):
        for sm in ((False, True) if seed < 12 else (True,)):
            arms = paired(seed, sm)
            magnitudes = [[min(x,P-x) for x,_ in pts] for pts in arms]
            assert magnitudes[0] == magnitudes[1] == magnitudes[2]
            assert len(set(magnitudes[0])) == 500
            digest = hashlib.sha256(",".join(map(str,magnitudes[0])).encode()).hexdigest()
            for name, pts in zip(("aux","twist","random_sign"), arms):
                writer.writerow(["initial" if seed < 12 else "confirmation",seed,int(sm),
                                 name,*census(pts),digest])


if __name__ == "__main__":
    main()
