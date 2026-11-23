"""Exhaustive aggregate coverage on a fixed public coordinate set."""
from collections import Counter
from itertools import combinations_with_replacement
import json
from math import comb
from pathlib import Path
import subprocess

p = 2**31-1
rev = "8dc1be894"
src = "experiments/prime-field-auxiliary-ic/snapshot"
def read(path):
    return subprocess.check_output(["git","show",f"{rev}:{src}/{path}"],cwd=Path(__file__).parent)

ns = dict(__name__="archive", __file__="prepare.py")
exec(compile(read("prepare.py"),"prepare.py","exec"),ns)
curve = ns["Curve"](p,a4=2,a6=14)
primes = [q for q in range(2,212) if all(q%d for d in range(2,int(q**0.5)+1))]
def smooth(x):
    assert x>0
    for q in primes:
        while x%q==0:
            x//=q
    return x==1

def census(points):
    signed=[s for pt in points for s in (pt,curve.neg(pt))]
    m=len(points)
    visited=bytearray((p+7)//8)
    seen=0
    cancelled=0
    infinity=0
    pair_x=set()
    for i, a in enumerate(signed):
        for j in range(i,len(signed)):
            b=signed[j]
            ab=curve.add(a,b)
            if ab is not None:
                pair_x.add(ab[0])
            for k in range(j,len(signed)):
                if i^1==j or i^1==k or j^1==k:
                    cancelled+=1
                    continue
                result=curve.add(ab,signed[k])
                if result is None:
                    infinity+=1
                    continue
                x=result[0]
                index=x>>3
                bit=1<<(x&7)
                if not visited[index]&bit:
                    visited[index]|=bit
                    seen+=1
    assert cancelled==2*m*m
    def covered(x):
        return bool(visited[x>>3] & (1<<(x&7)))
    base_overlap=2*sum(covered(x) for x,y in points)
    return dict(liftable_x=m,triples=comb(2*m+2,3),cancelling_triples=cancelled,
                noncancelling_infinity=infinity,noncancelling_finite_sums=2*seen,
                noncancelling_base_overlap=base_overlap,
                all_finite_sums=2*seen+2*m-base_overlap,
                two_point_sums=2*len(pair_x),noncancelling_two_point_overlap=2*sum(map(covered,pair_x)))

report={}
for base in ("structured","random"):
    path=f"algebraic/structure_results/field31_s15/{base}_roots.json"
    pts=[]
    for x in json.loads(read(path)):
        if not smooth(min(x,p-x)): continue
        rhs=(x**3+2*x+14)%p
        y=pow(rhs,(p+1)//4,p)
        if y*y%p==rhs: pts.append((x,min(y,p-y)))
    assert len(pts)=={"structured":195,"random":166}[base]
    report[base]=census(pts)
# Positive control has cancellations, equal sums and signed triples summing to infinity.
P=pts[0]
control=[curve.mul(k,P) for k in (1,2,3)]
measured=census(control)
signed=control+[curve.neg(pt) for pt in control]
full=Counter(curve.add(curve.add(a,b),c) for a,b,c in combinations_with_replacement(signed,3))
assert full[None]==measured["noncancelling_infinity"]>0
assert len(full)-1==measured["all_finite_sums"] and measured["noncancelling_base_overlap"]>0
report["control"]=measured
print(json.dumps(report,indent=2))
