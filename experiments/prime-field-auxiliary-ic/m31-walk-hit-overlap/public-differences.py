"""Test whether distinct signed coefficient differences coincide on the public curve."""
from collections import Counter
from itertools import combinations_with_replacement
import json
import subprocess

fixture = ("4551d77ae4a87fdee717e69b8f90c46420f6cc35:"
           "experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/results/"
           "field31_s5_base0/public.json")
data = json.loads(subprocess.check_output(["git", "show", fixture]))
curve = data["public"]
p = curve["p"]


def neg(point):
    x, y = point
    return x, -y % p


def add(a, b):
    x, y = a
    z, w = b
    if x == z and (y + w) % p == 0:
        return None
    if x == z:
        num, den = 3*x*x + curve["a"], 2*y
    else:
        num, den = w-y, z-x
    slope = num * pow(den, -1, p) % p
    u = (slope*slope-x-z) % p
    return u, (slope*(x-u)-y) % p


# Differences have coefficients in [-4,4], so balanced radix nine is injective.
basis = [(9**i, tuple(point)) for i, point in enumerate(data["factor_base"])]
signed = basis + [(-k, neg(point)) for k, point in basis]
hits = {}
for (i, a), (j, b) in combinations_with_replacement(signed, 2):
    point = add(a, b)
    assert (point is None) == (i+j == 0)
    if point is not None:
        assert hits.setdefault(i+j, point) == point
assert len(hits) == len(set(hits.values())) == 578

images, counts = {}, Counter()
for i, a in hits.items():
    for j, b in hits.items():
        delta = i-j
        point = add(a, neg(b))
        assert images.setdefault(delta, point) == point
        counts[delta] += 1
assert len(images) == len(set(images.values()))
assert images[0] is None and counts.pop(0) == 578
assert sum(counts.values()) == 578*577
print("multiplicity,nonzero_displacements")
for size, number in sorted(Counter(counts.values()).items()):
    print(f"{size},{number}")
