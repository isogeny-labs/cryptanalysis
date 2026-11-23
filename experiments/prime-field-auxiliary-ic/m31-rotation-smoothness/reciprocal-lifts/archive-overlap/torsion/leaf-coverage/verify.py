"""Independent leaf-by-leaf minimum-threshold calculation using SymPy factorization."""
from functools import cache
from itertools import product
from pathlib import Path
import json
import subprocess

from sympy import factorint

here = Path(__file__).resolve().parent
path = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/results/field31_s5_base0/public.json"
f = json.loads(subprocess.check_output(["git","show",f"efb9330c1:{path}"],cwd=here))
p = f["public"]["p"]
columns = {x for x,y in f["factor_base"]}

@cache
def orbit_bound(x):
    return min(max(factorint((x << i)%p),default=1) for i in range(31))

def cost_for_sign(x,y):
    if pow(x,(p-1)//2,p)!=p-1 or pow(x,31,p)==pow(y,31,p):
        return float("inf")
    return max(orbit_bound(x),orbit_bound(y))

rows = {}
for leaf in f["structured_roots"]:
    x = leaf
    row = []
    for step in f["auxiliary"]["maps"]:
        u = (x-step["r"])%p
        v = step["B"]*pow(u,-1,p)%p
        s = pow(pow(step["B"],-1,p),(p+1)//4,p)
        left = cost_for_sign((-s*u)%p,(-s*v)%p)
        right = cost_for_sign(s*u%p,s*v%p)
        row.append({0:float("inf"),-1:left,1:right,2:min(left,right)})
        x = (u+step["A"]+v)%p
    assert x == f["auxiliary"]["terminal_c"]
    rows[leaf] = row

receipt = json.loads((here/"result.json").read_text())
for choices,key in [((-1,0,1),"full_coverage_frontier"),((-1,0,1,2),"both_signs_frontier")]:
    first = float("inf")
    for signs in product(choices, repeat=5):
        entry = {x:min(level[sign] for level,sign in zip(row,signs)) for x,row in rows.items()}
        # For fixed signs, the largest entry threshold among required columns
        # is the earliest possible full coverage. Later bounds only add leaves.
        b = max(entry[x] for x in columns)
        if b < float("inf"):
            first = min(first,b)
            assert all(t <= b for t in entry.values())
    assert [(r["bound"],r["leaf_count"]) for r in receipt[key]] == [(first,len(rows))]
    print(len(choices)**5, "schedules checked; first full coverage at", first, "retains all", len(rows))
