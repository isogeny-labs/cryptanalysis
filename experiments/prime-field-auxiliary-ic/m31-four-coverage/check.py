"""Check the native aggregate counter against independent full affine-point sets."""
import csv
import io
from math import factorial, prod
from collections import Counter
from itertools import combinations_with_replacement
from pathlib import Path
import subprocess
import sys

p = 2**31 - 1
def add(a,b):
    if a is None: return b
    if b is None: return a
    x,y = a
    u,v = b
    if x == u and (y+v)%p == 0: return None
    slope = ((3*x*x+2)*pow(2*y,-1,p) if x==u else (y-v)*pow(x-u,-1,p))%p
    z = (slope*slope-x-u)%p
    return z,(slope*(x-z)-y)%p

def check(xs):
    signed = []
    for x in xs:
        rhs=(x**3+2*x+14)%p
        y=pow(rhs,(p+1)//4,p)
        assert y and y*y%p==rhs
        signed.extend([(x,y),(x,-y%p)])
    output=subprocess.check_output([sys.argv[1]],input=''.join(f'{x}\n' for x in xs),text=True)
    union=set()
    vectors = {(0,)*len(xs): None}
    for n,row in enumerate(csv.DictReader(io.StringIO(output)),1):
        sums=set()
        for combo in combinations_with_replacement(range(len(signed)),n):
            point=None
            coeff = [0]*len(xs)
            for idx in combo:
                point=add(point,signed[idx])
                coeff[idx//2] += 1 if idx%2==0 else -1
            assert vectors.setdefault(tuple(coeff),point) == point
            sums.add(point)
        union.update(sums)
        assert int(row['exact_finite'])==len(sums-{None})
        assert int(row['upto_finite'])==len(union-{None})
        assert int(row['exact_has_infinity'])==(None in sums)

    # Count one orientation per reduced vector using separately computed endpoints.
    prefixes = Counter()
    for vector, point in vectors.items():
        if sum(map(abs, vector)) != 4 or point not in signed:
            continue
        if next(value for value in vector if value) < 0:
            continue
        prefixes[24 // prod(factorial(abs(value)) for value in vector)] += 1
    raw = subprocess.check_output([sys.argv[1], "five-prefixes"],
        input="".join(f"{x}\n" for x in xs), text=True)
    rows = list(csv.DictReader(io.StringIO(raw)))
    assert [(int(r["prefix_permutations"]), int(r["completable_prefixes_up_to_sign"]))
            for r in rows] == [(w, prefixes[w]) for w in (1, 4, 6, 12, 24)]

    # Include the empty sum explicitly when translating a radius-four ball.
    union.add(None)
    shifted=union | {add(a,b) for a in signed[:2] for b in union}
    raw=subprocess.check_output([sys.argv[1],"translate",str(xs[0])],
        input="".join(f"{x}\n" for x in xs),text=True)
    assert raw.splitlines()[-1]==f"translated_union_finite,{len(shifted-{None})}"

    # Count the cumulative translates in both native enumeration orders.
    cover=union.copy()
    expected=[]
    for idx,x in enumerate(xs):
        for b in signed[2*idx:2*idx+2]:
            cover.update(add(a,b) for a in union)
        expected.append(f"{idx+1},{x},{len(cover-{None})}")
    explicit={None}
    for n in range(1,6):
        for combo in combinations_with_replacement(signed,n):
            point=None
            for term in combo: point=add(point,term)
            explicit.add(point)
    assert cover==explicit
    for mode in ("five","five-reverse"):
        raw=subprocess.check_output([sys.argv[1],mode],
            input="".join(f"{x}\n" for x in xs),text=True)
        assert raw.splitlines()[5:]==expected

    counts = Counter(vectors.values())
    identity = counts.pop(None)
    histogram = Counter(counts.values())
    raw = subprocess.check_output([sys.argv[1],"multiplicity"],
        input="".join(f"{x}\n" for x in xs),text=True)
    rows = list(csv.DictReader(io.StringIO(raw)))
    assert histogram == {int(row["multiplicity"]):int(row["finite_points"]) for row in rows}
    assert all(int(row["identity_vectors"])==identity for row in rows)

    ordered = Counter({None: 1})
    for _ in range(4):
        ends = Counter()
        for point, paths in ordered.items():
            for step in signed:
                ends[add(point,step)] += paths
        ordered = ends
    distribution = Counter(ordered.values())
    distribution[0] = 2147505293-len(ordered)
    raw = subprocess.check_output([sys.argv[1],"walk-four"],
        input="".join(f"{x}\n" for x in xs),text=True)
    assert distribution == {int(row["ordered_walks"]):int(row["group_points"])
                            for row in csv.DictReader(io.StringIO(raw))}

    five = Counter()
    for point, paths in ordered.items():
        for step in signed:
            five[add(point,step)] += paths
    raw = subprocess.check_output([sys.argv[1],"walk-five-sample"],
        input="".join(f"{x}\n" for x in xs),text=True)
    for row in csv.DictReader(io.StringIO(raw)):
        assert int(row["five_return_paths"]) == five[None]
        assert int(row["six_return_paths"]) == sum(five[step] for step in signed)

basis=list(map(int,(Path(__file__).resolve().parent.parent/'m31-basis-mask/coordinates.txt').read_text().splitlines()))
P=(3,417540811)
twice=add(P,P)
check([P[0],twice[0],add(P,twice)[0]])
check(basis[:9])
check(basis[::23])
