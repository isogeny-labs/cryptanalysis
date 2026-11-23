"""Enumerate all pair collisions of projective involutions on the pinned public fixture."""
from collections import Counter, defaultdict
from itertools import combinations
from functools import reduce
from operator import xor
import json
import re
import sys
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
FIXTURE = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/results/field31_s5_base0/public.json"
raw = subprocess.check_output(["git", "show", f"efb9330c1:{FIXTURE}"], cwd=HERE)
fixture = json.loads(raw)
p = 2**31 - 1
xs = fixture["structured_roots"]
assert (fixture["public"]["p"], fixture["public"]["a"], fixture["public"]["b"]) == (p, 2, 14)
assert len(set(xs)) == len(xs) == 32 and all(0 <= x < p for x in xs)
lean = (HERE / "FixtureHash.lean").read_text()
root_literal = re.search(r"def roots : List F := (\[[0-9,\s]+\])", lean)
assert root_literal and json.loads(root_literal[1]) == xs
labels = {x: pow((x**3 + 2*x + 14) % p, (p-1)//2, p) == 1 for x in xs}
assert {x for x in xs if labels[x]} == {x for x, _ in fixture["factor_base"]}
if sys.argv[1:] == ["--decode-input"]:
    for x in xs:
        print(x, int(labels[x]))
    sys.exit(0)
if sys.argv[1:]:
    sys.exit("usage: fixture_hash.py [--decode-input]")

pairs = [(x, y, (x+y) % p, x*y % p) for x, y in combinations(xs, 2)]
assert len(set(s for _, _, s, _ in pairs)) == len(pairs) == 496
affine = Counter(int(labels[x] != labels[y]) for x, y, _, _ in pairs)

# Every nonsingular involution exchanging two disjoint pairs is found once
# per pair of incident chords. Keep the chord indices for the complete orbit census.
maps = defaultdict(set)
for (i, (x, y, s, t)), (j, (u, v, w, q)) in combinations(enumerate(pairs), 2):
    if x == u or x == v or y == u or y == v:
        continue
    a = (q-t) * pow(w-s, -1, p) % p
    b = (t-a*s) % p
    assert (a*a+b) % p
    maps[a,b].update((i,j))

histogram = Counter()
witness = {}
for (a,b), indices in maps.items():
    mixed = 0
    for i in indices:
        x,y,_,_ = pairs[i]
        assert (x-a) % p and (a*x+b) * pow(x-a,-1,p) % p == y
        mixed += labels[x] != labels[y]
    cell = (len(indices), mixed)
    histogram[cell] += 1
    witness.setdefault(cell, (a,b))

best = max(n for n, mixed in histogram if mixed == 0)
a,b = witness[best,0]
# Independent direct application at the best lossless example and at inversion.
def check(a,b):
    buckets = defaultdict(list)
    for x in xs:
        mate = ((a*x+b) * pow((x-a) % p,-1,p)) % p if x != a else p
        buckets[min(x,mate)].append(labels[x])
    return len(buckets), sum(len(set(v)) == 2 for v in buckets.values())

assert check(a,b) == (32-best,0)
assert check(0,1) == (16,7)
# Enumerate masks by weight using one syndrome bit per reciprocal pair.
reciprocal = list(zip(xs[:16], xs[16:], strict=True))
assert all(x*y % p == 1 for x,y in reciprocal)
columns = [sum((((x ^ y) >> bit) & 1) << i for i,(x,y) in enumerate(reciprocal)) for bit in range(31)]
wanted = sum((labels[x] != labels[y]) << i for i,(x,y) in enumerate(reciprocal))
for weight in range(5):
    masks = [bits for bits in combinations(range(31), weight)
             if reduce(xor, (columns[j] for j in bits), 0) == wanted]
    if masks:
        break
assert masks and weight == 4
mask = sum(1 << j for j in masks[0])
bits = sum((labels[x] ^ ((x & mask).bit_count() % 2)) << i for i,x in enumerate(xs[:16]))
assert all(bool(((bits >> (i%16)) & 1) ^ ((x & mask).bit_count() % 2)) == labels[x]
           for i,x in enumerate(xs))

print(json.dumps({
    "root_count": len(xs), "liftable": sum(labels.values()),
    "affine_centers": {"no_pair": p-len(pairs), "one_equal_pair": affine[0], "one_mixed_pair": affine[1]},
    "nonaffine_maps_with_multiple_pairs": [
        {"pairs": n, "errors": e, "maps": count} for (n,e),count in sorted(histogram.items())],
    "minimum_parity_weight": weight, "minimum_parity_masks": masks,
    "corrected_orbit_bits": bits,
    "maximum_lossless_pairs": best, "lossless_witness": {"a": a, "b": b},
    "witness_pairs": [pairs[i][:2] for i in sorted(maps[a,b])],
}, indent=2))
