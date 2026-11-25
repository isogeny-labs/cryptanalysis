"""Measure complete public basis preparation and compare group-operation counts."""
import csv
import ctypes as C
import hashlib
import json
from itertools import permutations
from pathlib import Path
import subprocess
import sys
from time import perf_counter_ns, process_time_ns

here = Path(__file__).resolve().parent
prefix = "experiments/prime-field-auxiliary-ic/snapshot/"
archive = "efb9330c1ee7e30743b7674f686cccb49f1cb25e"
previous = "df1fadc5d"

def read(revision, path):
    return subprocess.check_output(["git","show",f"{revision}:{prefix}{path}"],cwd=here)

def load(raw):
    scope = {"__name__":"public_basis","__file__":"prepare.py"}
    exec(compile(raw,"prepare.py","exec"),scope)
    return scope

sources = {"archive":read(archive,"prepare.py"),"siblings":read(previous,"prepare.py"),
           "shared":(here.parents[2]/"snapshot/prepare.py").read_bytes()}
assert hashlib.sha256(sources["siblings"]).hexdigest() == "2d838e93f17850b6da67091ce22d7e2f489529316b4ae1bcce578b842f0e1bf8"
modules = {name:load(raw) for name,raw in sources.items()}
p = 2**31-1
manifest = json.loads(read(archive,"algebraic/optimized/results/field31_s5_base0/public.json"))
for k in (5,7,13,17,19,31,61):
    for depth in sorted({1,min(5,k-2),min(9,k-2)}):
        for limit in (0,3,None):
            kwargs = dict(root_limit=limit)
            assert modules["shared"]["chain"](2**k-1,depth,**kwargs) == modules["siblings"]["chain"](2**k-1,depth,**kwargs)

def counts(raw):
    ns = load(raw)
    curve = ns["Curve"]
    add = curve.add
    tally = dict(add_calls=0,inversions=0)
    def counted_add(self,a,b):
        tally["add_calls"] += 1
        return add(self,a,b)
    def counted_pow(x,n,p):
        tally["inversions"] += (n == -1)
        return pow(x,n,p)
    curve.add = counted_add
    ns["pow"] = counted_pow
    ns["chain"](p,5,enumerate_all=True)
    return tally

print(json.dumps({name:counts(s) for name,s in sources.items()}),file=sys.stderr)

words = C.c_uint32*32
fn = C.CDLL(str(Path(sys.argv[1]).resolve())).m31_lift32
fn.argtypes = [C.POINTER(C.c_uint32)]*2
fn.restype = None
def native(xs):
    ys = words()
    fn(words(*xs),ys)
    return [[x,y] for x,y in zip(xs,ys) if y != p]

def python(xs):
    result = []
    for x in xs:
        rhs = (x**3+2*x+14)%p
        y = pow(rhs,(p+1)//4,p)
        if y*y%p == rhs:
            result.append([x,min(y,p-y)])
    return result

arms = {"original":(modules["archive"]["chain"],python),
        "siblings_native":(modules["siblings"]["chain"],native),
        "shared_native":(modules["shared"]["chain"],native)}
expected = python(manifest["structured_roots"])
assert sorted(expected) == manifest["factor_base"]
writer = csv.writer(sys.stdout,lineterminator="\n")
writer.writerow(("block","position","arm","calls","wall_ns","cpu_ns"))
for block,order in enumerate(list(permutations(arms))*4):
    for pos,name in enumerate(order):
        chain,lift = arms[name]
        wall,cpu = perf_counter_ns(),process_time_ns()
        for _ in range(32):
            aux,xs = chain(p,5,enumerate_all=True)
            points = lift(xs)
        ct,wt = process_time_ns()-cpu,perf_counter_ns()-wall
        assert xs == manifest["structured_roots"] and json.loads(json.dumps(aux)) == manifest["auxiliary"]
        assert points == expected
        writer.writerow((block,pos,name,32,wt,ct))
