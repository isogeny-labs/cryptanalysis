"""Replay the public preparation entry point and measure the two changes factorially."""
import csv
import ctypes as C
import hashlib
from itertools import permutations
from pathlib import Path
import json
import subprocess
import sys
from time import perf_counter_ns, process_time_ns

here = Path(__file__).resolve().parent
src = here.parents[2] / "snapshot/prepare.py"
prefix = "experiments/prime-field-auxiliary-ic/snapshot/"
rev = "efb9330c1ee7e30743b7674f686cccb49f1cb25e"
def pinned(path, digest):
    raw = subprocess.check_output(["git","show",f"{rev}:{prefix}{path}"],cwd=here)
    assert hashlib.sha256(raw).hexdigest() == digest
    return raw

def load(source):
    ns = {"__file__": str(src), "__name__": "public_basis"}
    exec(compile(source,str(src),"exec"),ns)
    return ns

old = load(pinned("prepare.py","2371663a53663a158a5e4faa87833efe888d0ae54f641d72a230e1a183ec7959"))
new = load(src.read_bytes())
fixture = json.loads(pinned("algebraic/optimized/results/field31_s5_base0/public.json",
                            "a5fd508b6deacd2e2036a790946d7700929a822caf92e1fed699e6a7657fb9ca"))
p = 2**31-1
for depth in (1,2,5,8,10):
    for limit in (None,0,3,2**depth-1):
        assert old["chain"](p,depth,root_limit=limit) == new["chain"](p,depth,root_limit=limit)
assert old["chain"](2**61-1,5) == new["chain"](2**61-1,5)
maps = fixture["auxiliary"]["maps"]
terminal = fixture["auxiliary"]["terminal_c"]
xs = fixture["structured_roots"]
check = new["_check_sibling_fiber"]
assert check(xs,maps,terminal,p)
for i in range(len(xs)):
    altered = xs.copy()
    altered[i] = (altered[i]+1)%p
    assert not check(altered,maps,terminal,p)
assert not check(xs,maps,(terminal+1)%p,p)
assert not check(xs[:-1],maps,terminal,p)

def python_lift(xs):
    result = []
    for x in xs:
        rhs = (x**3+2*x+14)%p
        y = pow(rhs,(p+1)//4,p)
        if y*y%p == rhs:
            result.append([x,min(y,p-y)])
    return result

fn = C.CDLL(str(Path(sys.argv[1]).resolve())).m31_lift32
fn.argtypes = [C.POINTER(C.c_uint32)]*2
fn.restype = None
words = C.c_uint32*32
def native_lift(xs):
    x,y = words(*xs),words()
    fn(x,y)
    return [[v,r] for v,r in zip(xs,y) if r != p]

arms = {"direct_python":(old["chain"],python_lift),"direct_native":(old["chain"],native_lift),
        "paired_python":(new["chain"],python_lift),"paired_native":(new["chain"],native_lift)}
reference = python_lift(xs)
assert sorted(reference) == fixture["factor_base"]
writer = csv.writer(sys.stdout,lineterminator="\n")
writer.writerow(("block","position","arm","calls","wall_ns","cpu_ns"))
for block, order in enumerate(permutations(arms)):
    for pos,name in enumerate(order):
        chain,lift = arms[name]
        wall,cpu = perf_counter_ns(),process_time_ns()
        for _ in range(24):
            aux,roots = chain(p,5,enumerate_all=True)
            points = lift(roots)
        ct,wt = process_time_ns()-cpu,perf_counter_ns()-wall
        assert roots == xs and json.loads(json.dumps(aux)) == fixture["auxiliary"] and points == reference
        writer.writerow((block,pos,name,24,wt,ct))
