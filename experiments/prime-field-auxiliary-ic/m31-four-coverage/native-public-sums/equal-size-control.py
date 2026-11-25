"""Compare unsigned signed-pair-sum coordinates on equal-size public bases."""
from collections import Counter
from hashlib import sha256
from itertools import combinations

P = 2**31 - 1
WIDTH = 34


def public_basis(seed):
    points = {}
    counter = 0
    while len(points) < WIDTH:
        label = f"m31-equal-size-v1/{seed}/{counter}".encode("ascii")
        counter += 1
        x = int.from_bytes(sha256(label).digest()[:4], "big") & P
        if x == P or x in points:
            continue
        rhs = (x**3 + 2*x + 14) % P
        y = pow(rhs, (P+1)//4, P)
        if y*y % P == rhs and y:
            points[x] = min(y, P-y)
    return list(points.items())


def check_basis(points):
    keys = []
    for x, y in points:
        slope = (3*x*x + 2) * pow(2*y, -1, P) % P
        keys.append((slope*slope - 2*x) % P)
    for (x, y), (u, v) in combinations(points, 2):
        inverse = pow(u-x, -1, P)
        for signed_v in (v, -v):
            slope = (signed_v-y) * inverse % P
            keys.append((slope*slope-x-u) % P)
    assert len(keys) == WIDTH**2
    return len(set(keys))


if __name__ == "__main__":
    counts = Counter(check_basis(public_basis(seed)) for seed in range(1024))
    for distinct, frequency in sorted(counts.items()):
        print(f"{distinct} distinct coordinates: {frequency} bases")
