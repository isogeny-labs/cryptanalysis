"""Directly enumerate all sign-normalized four-point relations on small prime groups."""
from itertools import combinations, product
from math import comb
from fractions import Fraction

for n in (11, 13, 17, 19, 23, 29, 31, 37, 41, 43):
    orbits = range(1, (n+1)//2)
    total = sum((a+i*b+j*c+k*d) % n == 0
                for a,b,c,d in combinations(orbits,4)
                for i,j,k in product((-1,1),repeat=3))
    assert Fraction(total, comb(len(orbits),4)) == Fraction(8,n-3)
    print(n, total)
print(Fraction(8*comb(500,4),2147505293-3))
