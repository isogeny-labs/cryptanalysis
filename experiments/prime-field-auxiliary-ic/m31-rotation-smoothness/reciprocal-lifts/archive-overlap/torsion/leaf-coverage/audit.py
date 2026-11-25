"""Trace public fiber nodes to their leaves and enumerate common scale choices."""
from collections import defaultdict
from functools import cache
from itertools import product
from pathlib import Path
from math import isqrt
import hashlib
import json
import subprocess

here = Path(__file__).resolve().parent
receipt = json.loads((here.parent.parent/"result.json").read_text())
path = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/results/field31_s5_base0/public.json"
raw = subprocess.check_output(["git","show",f"{receipt['archive']}:{path}"],cwd=here)
assert hashlib.sha256(raw).hexdigest() == receipt["fixture_sha256"]
fixture = json.loads(raw)
p = 2**31-1
roots = fixture["structured_roots"]
columns = {x for x,y in fixture["factor_base"]}
rhs = lambda x: (x**3+2*x+14) % p
assert columns == {x for x in roots if pow(rhs(x),(p-1)//2,p) != p-1}
primes = []
for d in range(2,isqrt(p)+1):
    if all(d%q for q in primes if q*q <= d):
        primes.append(d)

def largest_factor(x):
    largest = 1
    for q in primes:
        if q*q > x:
            break
        while x%q == 0:
            largest = q
            x //= q
    return max(largest,x)

@cache
def minimum_bound(x):
    return min(largest_factor((x << i) % p) for i in range(31))

def expand(mask):
    return sorted(x for j,x in enumerate(roots) if mask >> j & 1)

column_mask = sum(1 << i for i,x in enumerate(roots) if x in columns)
nodes = {x:1 << i for i,x in enumerate(roots)}
levels = []
events = set()
for step in fixture["auxiliary"]["maps"]:
    b = step["B"]
    scale = pow(pow(b,-1,p),(p+1)//4,p)
    assert scale*scale*b % p == 1
    parents = defaultdict(list)
    for x,mask in nodes.items():
        u = (x-step["r"]) % p
        parents[(u+step["A"]+b*pow(u,-1,p))%p].append((u,mask))
    level = []
    nodes = {}
    for parent, children in sorted(parents.items()):
        (u,mu),(v,mv) = sorted(children)
        assert u*v % p == b and not mu&mv
        nodes[parent] = mu|mv
        for sign in (-1,1):
            x,y = sign*scale*u%p,sign*scale*v%p
            assert x*y%p == 1
            if pow(x, (p-1)//2,p) != p-1 or pow(x,62,p) == 1:
                continue
            bound = max(minimum_bound(x), minimum_bound(y))
            level.append((bound,sign,mu|mv))
            events.add(bound)
    levels.append(level)
assert nodes == {fixture["auxiliary"]["terminal_c"]:(1 << len(roots))-1}

def choices(bound, allow_both=False):
    selections = []
    for level in levels:
        masks = {-1:0,0:0,1:0}
        for threshold,sign,leaves in level:
            if threshold <= bound:
                masks[sign] |= leaves
        masks[2] = masks[-1] | masks[1]
        selections.append(masks)
    for signs in product((-1,0,1,2) if allow_both else (-1,0,1),repeat=len(levels)):
        leaves = 0
        for idx,sign in enumerate(signs):
            leaves |= selections[idx][sign]
        yield signs,leaves

def record(bound, signs, leaves):
    return dict(bound=bound,signs=signs,leaf_count=leaves.bit_count(),
                lifted_count=(leaves&column_mask).bit_count(),leaves=expand(leaves))

def frontier(allow_both):
    result = []
    for bound in sorted(events):
        feasible = [(m.bit_count(),s,m) for s,m in choices(bound,allow_both)
                    if (m&column_mask)==column_mask]
        if feasible:
            count,signs,mask = min(feasible)
            if not result or count < result[-1]["leaf_count"]:
                result.append(record(bound,signs,mask))
    return result

best211 = max(choices(211),key=lambda e:(e[1]&column_mask).bit_count())
print(json.dumps(dict(archive_sha256=receipt["fixture_sha256"],root_count=len(roots),column_count=len(columns),
    event_count=len(events),schedules=3**len(levels),best211=record(211,*best211),
    retained_columns_at_211=expand(best211[1]&column_mask),full_coverage_frontier=frontier(False),both_signs_frontier=frontier(True)),indent=2))
