"""Check the native aggregate counter against independent full affine-point sets."""
import csv
import io
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
    for n,row in enumerate(csv.DictReader(io.StringIO(output)),1):
        sums=set()
        for combo in combinations_with_replacement(signed,n):
            point=None
            for term in combo: point=add(point,term)
            sums.add(point)
        union.update(sums)
        assert int(row['exact_finite'])==len(sums-{None})
        assert int(row['upto_finite'])==len(union-{None})
        assert int(row['exact_has_infinity'])==(None in sums)

basis=list(map(int,(Path(__file__).resolve().parent.parent/'m31-basis-mask/coordinates.txt').read_text().splitlines()))
P=(3,417540811)
twice=add(P,P)
check([P[0],twice[0],add(P,twice)[0]])
check(basis[:9])
check(basis[::23])
