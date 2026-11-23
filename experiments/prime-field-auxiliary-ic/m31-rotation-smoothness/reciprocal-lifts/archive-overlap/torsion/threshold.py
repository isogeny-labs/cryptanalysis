"""Least smoothness bound for a reciprocal-compatible sibling hit."""
from functools import cache
from math import isqrt
import json
from pathlib import Path
import subprocess

here = Path(__file__).resolve().parent
prior = json.loads((here / "result.json").read_text())
path = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/results/field31_s5_base0/public.json"
fixture = json.loads(subprocess.check_output(["git","show",f"{prior['archive']}:{path}"], cwd=here))
p = fixture["auxiliary"]["p"]
primes = []
for n in range(3, isqrt(p)+1, 2):
    if all(n % q for q in primes if q*q <= n):
        primes.append(n)


def largest_odd_prime(n):
    while n % 2 == 0:
        n //= 2
    largest = 1
    for q in primes:
        if q*q > n:
            break
        while n % q == 0:
            largest = q
            n //= q
    return max(largest, n)


@cache
def minimum_bound(canonical):
    return min(largest_odd_prime((canonical << i) % p) for i in range(31))


def orbit_bound(x):
    return minimum_bound(min((x << i) % p for i in range(31)))


xs = fixture["structured_roots"]
results = []
for step in fixture["auxiliary"]["maps"]:
    b = step["B"]
    us = {(x-step["r"]) % p for x in xs}
    pairs = [(u,v) for u in us if u < (v := b*pow(u,-1,p) % p)]
    # All 62 compatible scales form two 31-rotation orbits; use ±sqrt(1/B).
    scale = pow(pow(b,-1,p), (p+1)//4, p)
    assert scale*scale*b % p == 1
    best = None
    for s in (scale, p-scale):
        for u,v in pairs:
            x,y = s*u % p, s*v % p
            assert x*y % p == 1
            if pow(x,(p-1)//2,p) != p-1 or pow(x,62,p) == 1:
                continue
            bx, by = orbit_bound(x), orbit_bound(y)
            candidate = (max(bx,by),s,u,v,bx,by)
            if best is None or candidate < best:
                best = candidate
    results.append(best)
    xs = [(u+v+step["A"]) % p for u,v in pairs]
assert xs == [fixture["auxiliary"]["terminal_c"]]
print(json.dumps([dict(bound=h,scale=s,u=u,v=v,first_bound=a,second_bound=b)
                  for h,s,u,v,a,b in results], indent=2))
