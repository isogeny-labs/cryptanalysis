"""Recheck orbit keys and compute every phase using independent GMP characters."""
import csv
from pathlib import Path
import subprocess
import sys

from gmpy2 import jacobi

p = 2**31-1
pairs, oracle = [str(Path(arg).resolve()) for arg in sys.argv[1:]]
xs = list(map(int,subprocess.check_output([pairs]).splitlines()))
keys = sorted(pow(x,31,p) for x in xs)
assert keys == list(map(int,subprocess.check_output([oracle]).splitlines()))
assert len(keys) == 104580

def masks(x, step):
    masks = [0,0,0]
    for i in range(31):
        cube = pow(x,3,p)
        for j,rhs in enumerate((cube+x,cube+2*x+14,cube+2*x-14)):
            masks[j] |= int(jacobi(rhs,p) >= 0) << i
        x = x*step % p
    a,b,c = masks
    return (a,b,c,a&b,a&c)

sums = [[0]*5 for _ in range(31)]
for x in xs:
    left = masks(x,2)
    right = list(masks(pow(x,-1,p),(p+1)//2))
    assert left[0] == right[0]
    for row in sums:
        for j in range(5):
            row[j] += (left[j] & right[j]).bit_count()
            right[j] = ((right[j] << 1) & p) | (right[j] >> 30)
writer = csv.writer(sys.stdout,lineterminator="\n")
writer.writerow(("phase","coordinates","aux_joint","curve_joint","twist_joint","aux_curve_joint","aux_twist_joint"))
for i,row in enumerate(sums):
    writer.writerow((i,31*len(xs),*row))
