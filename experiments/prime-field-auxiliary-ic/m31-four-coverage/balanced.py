"""Compare measured returns with formal sign cancellation and the random-basis mean."""
from collections import Counter
from fractions import Fraction
from itertools import combinations_with_replacement, product
from math import comb, factorial, prod
from pathlib import Path
import csv
import sys

here = Path(__file__).resolve().parent
order = 2147505293

def recurrence(m, k):
    counts = [1] + [0]*k
    for _ in range(m):
        counts = [sum(comb(2*r,2*j)*comb(2*j,j)*counts[r-j] for j in range(r+1))
                  for r in range(k+1)]
    return counts

def partitions(m, k):
    # Choose used generators; assign positive multiplicities; permute the signed letters.
    total = 0
    for size in range(1,min(m,k)+1):
        for mult in combinations_with_replacement(range(1,k+1),size):
            if sum(mult) != k:
                continue
            assignments = factorial(size)//prod(factorial(n) for n in Counter(mult).values())
            orderings = factorial(2*k)//prod(factorial(j)**2 for j in mult)
            total += comb(m,size)*assignments*orderings
    return total

for m in range(1,4):
    counts = recurrence(m,4)
    for k in range(1,5):
        brute = sum(all(w.count(2*i)==w.count(2*i+1) for i in range(m))
                    for w in product(range(2*m),repeat=2*k))
        assert counts[k] == partitions(m,k) == brute

with (here/"walk-four.csv").open() as f:
    bins = {int(r["ordered_walks"]): int(r["group_points"]) for r in csv.DictReader(f)}
# The zero vector is the only vector of weight at most four mapping to the identity.
with (here/"multiplicity.csv").open() as f:
    assert {int(r["identity_vectors"]) for r in csv.DictReader(f)} == {1}
counts = recurrence(195,4)
assert bins[counts[2]] == 1
with (here/"walk-five-sample.csv").open() as f:
    returns56 = {(int(r["five_return_paths"]),int(r["six_return_paths"])) for r in csv.DictReader(f)}
(five,six), = returns56
totals = {4:counts[2],5:five,6:six,8:sum(k*k*n for k,n in bins.items())}
writer = csv.writer(sys.stdout,lineterminator="\n")
writer.writerow(("steps","observed_returns","balanced_returns","nonbalanced_returns","random_basis_ratio"))
for steps,observed in totals.items():
    balanced = 0 if steps%2 else counts[steps//2]
    if steps%2==0: assert balanced == partitions(195,steps//2)
    nonbalanced = observed-balanced
    ratio = Fraction(nonbalanced*order,390**steps-balanced)
    writer.writerow((steps,observed,balanced,nonbalanced,format(float(ratio),".10f")))
