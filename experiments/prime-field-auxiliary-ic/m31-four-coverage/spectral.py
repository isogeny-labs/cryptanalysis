"""Exact arithmetic certificate for the Fourier bound from walk-four.csv."""
import csv
from fractions import Fraction
from pathlib import Path

here = Path(__file__).resolve().parent
with (here / "walk-four.csv").open() as stream:
    bins = [(int(r["ordered_walks"]), int(r["group_points"])) for r in csv.DictReader(stream)]
n = 2147505293
paths = 390**4
assert sum(count for _, count in bins) == n
assert sum(k*count for k, count in bins) == paths

def outside(cap):
    # Fill the available arc positions with the highest multiplicities first.
    available, inside = cap, 0
    for k, count in sorted(bins, reverse=True):
        take = min(available, count)
        inside += k*take
        available -= take
    assert available == 0
    return paths-inside

loss, previous = 0, 0
for j in range(1,25):
    x = Fraction(3*j,128)
    lower_sine = x-x**3/6
    price = int(10**6 * 2 * lower_sine**2)
    assert price >= previous
    cap = 1 + 2*((n*j-1)//128)
    loss += (price-previous)*outside(cap)
    previous = price
four = 1-Fraction(loss,10**6 * paths)
chi4 = Fraction(n*sum(k*k*count for k,count in bins),paths**2)-1
print("loss numerator",loss,"fourth power bound",four)
print("eigenvalue upper bound",float(four)**0.25)
assert four < Fraction(9641,10000)**4
for denom in (4,100,1000,1000000):
    t = 4
    while chi4**2 * four**(t-4) * denom**4 > 16:
        t += 1
    print("TV <=",Fraction(1,denom),"by step",t)
