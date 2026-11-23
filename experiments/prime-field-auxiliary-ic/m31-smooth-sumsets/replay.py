"""Exact finite sumset counts for fixed public coordinate sets."""
from collections import Counter
from itertools import combinations_with_replacement
from pathlib import Path
import csv
import json
import random
import subprocess
import sys

p = 2**31-1
prime_order = 2147505293
primes = [q for q in range(2,212) if all(q % d for d in range(2,int(q**0.5)+1))]
source = "experiments/prime-field-auxiliary-ic/snapshot"
revision = "6aca0149f747fd8466ead82bec5cb08d2dd9fc55"
def read(path):
    return subprocess.check_output(["git","show",f"{revision}:{source}/{path}"],
                                   cwd=Path(__file__).resolve().parent)

ns = dict(__name__="public_curve",__file__="prepare.py")
exec(compile(read("prepare.py"),"prepare.py","exec"),ns)
curve = ns["Curve"](p,a4=2,a6=14)

def smooth(x):
    assert x > 0
    for q in primes:
        while x % q == 0:
            x //= q
    return x == 1

def count(points):
    signed = points + [curve.neg(pt) for pt in points]
    assert len(set(signed)) == 2*len(points)
    counts = Counter(curve.add(a,b) for a,b in combinations_with_replacement(signed,2))
    assert counts.pop(None) == len(points)
    assert sum(counts.values()) == 2*len(points)**2
    assert all(counts[curve.neg(pt)] == multiplicity for pt,multiplicity in counts.items())
    return len(counts), max(counts.values()), sum(m*(m-1)//2 for m in counts.values())

writer = csv.writer(sys.stdout,lineterminator="\n")
writer.writerow(("base","representative","arm","liftable_x","finite_pairs","distinct_finite_sums",
                 "max_multiplicity","colliding_pairs_of_representations","finite_target_population"))
for base in ("structured","random"):
    roots=json.loads(read(f"algebraic/structure_results/field31_s15/{base}_roots.json"))
    lifted=[]
    for x in roots:
        rhs=(x**3+2*x+14)%p
        y=pow(rhs,(p+1)//4,p)
        if y*y%p == rhs:
            lifted.append((x,min(y,p-y)))
    assert len(lifted)==16342
    # Sums of two elements in ±{P,2P,3P} cover exactly ±P through ±6P.
    control = [curve.mul(k,lifted[0]) for k in (1,2,3)]
    distinct,peak,collisions = count(control)
    assert distinct == 12 and peak > 1 and collisions > 0
    for rep in ("canonical","signed"):
        filtered=[pt for pt in lifted if smooth(pt[0] if rep=="canonical" else min(pt[0],p-pt[0]))]
        for arm in ("smooth","sample0","sample1","sample2"):
            pts=filtered if arm=="smooth" else random.Random(int(arm[-1])).sample(sorted(lifted),len(filtered))
            distinct,peak,collisions=count(pts)
            writer.writerow((base,rep,arm,len(pts),2*len(pts)**2,distinct,peak,collisions,prime_order-1))
