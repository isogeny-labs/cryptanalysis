"""Unconditioned public auxiliary fibers, full-coordinate lift labels, and signed smoothness."""
import csv
import json
import math
import subprocess
import sys

P = 2**31 - 1
BOUNDS = (256, 1024, 4096)
PRIMES = [n for n in range(2, 4097) if all(n % d for d in range(2, math.isqrt(n) + 1))]
GENERATOR = """
p=2^31-1; E=ellinit([1,0],p); G=[Mod(3,p),Mod(615668188,p)]; K=ellmul(E,G,2^26);
setrand(SEED);
for(i=1,1100,R=ellmul(E,G,2*random(2^24-1)+3);v=vector(32);for(k=1,32,v[k]=lift(R[1]);R=elladd(E,R,K));print(v))
"""


def smooth_bound(x):
    if x == 0:
        return P
    largest = 1
    for q in PRIMES:
        if q*q > x:
            break
        while x % q == 0:
            x //= q
            largest = q
    return max(largest, x)


def panel(seed, seen):
    raw = subprocess.check_output(["gp", "-fq"], input=GENERATOR.replace("SEED", str(seed)), text=True)
    counts = {(b, flag): [0, 0] for b in BOUNDS for flag in range(4)}
    accepted = 0
    for line in raw.splitlines():
        row = json.loads(line)
        if len(set(row)) != 32:
            raise ValueError("incomplete orbit")
        if seen.intersection(row):
            continue
        seen.update(row)
        for x in row:
            rhs = (x**3 + 2*x + 14) % P
            sign = pow(rhs, (P-1)//2, P)
            if sign not in (1, P-1):
                raise ValueError("ambiguous lift")
            pos, neg = smooth_bound(x), smooth_bound(P-x)
            for b in BOUNDS:
                flag = int(pos <= b) + 2*int(neg <= b)
                counts[b, flag][int(sign == 1)] += 1
        accepted += 1
        if accepted == 1024:
            return counts
    raise ValueError("insufficient disjoint rows")


if __name__ == "__main__":
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["seed", "bound", "smooth_mask", "twist", "base"])
    seen = set()
    for seed in (291163, 291164):
        for (bound, mask), counts in panel(seed, seen).items():
            writer.writerow([seed, bound, mask, *counts])
