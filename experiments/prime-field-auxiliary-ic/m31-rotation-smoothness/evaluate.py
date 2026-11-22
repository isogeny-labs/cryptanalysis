import csv
import subprocess
from fractions import Fraction
from pathlib import Path

p = 2**31 - 1
bounds = (7, 13, 23, 47)

def orbit_key(x):
    least = x
    for _ in range(30):
        x = ((2*x) & p) | (x >> 30)
        least = min(least, x)
    return least

# Odd smooth integers suffice because removing factors of two stays in the orbit.
values = [1]
minimum_bound = {}
for prime in (3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47):
    extra = []
    for v in values:
        v *= prime
        while v < p:
            extra.append(v)
            v *= prime
    values.extend(extra)
    if prime in bounds:
        for v in values:
            minimum_bound.setdefault(orbit_key(v), prime)

counts = [[[0, 0] for _ in (0, *bounds)] for _ in range(2)]
source = Path(__file__).with_name("fibers.gp")
receipt = subprocess.run(["gp", "-q", "-f", source], capture_output=True, text=True, check=True)
assert not receipt.stderr, receipt.stderr
fibers = {}
for seq, index, x, lift in csv.reader(receipt.stdout.splitlines()):
    seq, index, x, lift = map(int, (seq, index, x, lift))
    fibers.setdefault(index, []).append(x)
    fold = counts[int(seq > 4096)]
    minimum = minimum_bound.get(orbit_key(x), p)
    for threshold, cell in zip((0, *bounds), fold):
        if threshold == 0 or minimum <= threshold:
            cell[0] += 1
            cell[1] += lift
assert len(fibers) == 8192 and all(len(set(xs)) == 32 for xs in fibers.values())
best = max((i for i in range(1,5) if counts[0][i][0]), key=lambda i: Fraction(counts[0][i][1],counts[0][i][0]))
for split, rows in zip(("selection","holdout"), counts):
    for threshold, (n,lifts) in zip((0,*bounds),rows):
        print(split,threshold,n,lifts)
print("chosen",bounds[best-1])
