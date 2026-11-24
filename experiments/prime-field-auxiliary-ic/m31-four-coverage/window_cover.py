"""Read the public sample.gp JSON lines and find the smallest seven-bit window family."""
import json
import sys
from itertools import combinations
from collections import Counter

bases = []
p = 2**31 - 1
for line in sys.stdin:
    pairs = json.loads(line)
    assert len(pairs) == len(dict(pairs)) == 32
    assert all(0 <= x < p and y == (pow((x**3 + 2*x + 14) % p, (p-1)//2, p) != p-1)
               for x, y in pairs)
    keys = tuple(sorted(x for x, y in pairs if y))
    assert len(keys) == 17
    bases.append(keys)
assert len(bases) == len(set(bases)) == 256

def fits(keys, width, offset):
    return len({(x >> offset) % (1 << width) for x in keys}) == len(keys)

print("Frozen six-bit window:", sum(fits(keys, 6, 10) for keys in bases))
print("Minimum width:", sorted(Counter(next(w for w in range(5, 32)
      if any(fits(keys, w, s) for s in range(32-w))) for keys in bases).items()))
covers = [sum(1 << i for i, keys in enumerate(bases) if fits(keys, 7, s))
          for s in range(25)]
for size in range(1, 26):
    best = 0
    for family in combinations(range(25), size):
        mask = 0
        for s in family:
            mask |= covers[s]
        if mask.bit_count() > best:
            best, witness = mask.bit_count(), family
        if best == 256:
            break
    print(size, best, witness)
    if best == 256:
        break
