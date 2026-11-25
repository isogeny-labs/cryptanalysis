"""Compare full ordered M31 bases with the same native ordinate calculation."""
import csv
import ctypes as C
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter_ns, process_time_ns

here = Path(__file__).resolve().parent
source_path = "experiments/prime-field-auxiliary-ic/snapshot/prepare.py"
previous = "150caa1b46b966e935df6e14392f2234d567d910"
def read(rev,path):
    return subprocess.check_output(["git","show",f"{rev}:{path}"],cwd=here)
def load(raw):
    ns = {"__name__":"public_chain","__file__":source_path}
    exec(compile(raw,source_path,"exec"),ns)
    return ns
sources = {"scalar":read(previous,source_path),"layer":(here.parents[2]/"snapshot/prepare.py").read_bytes()}
modules = {k:load(raw) for k,raw in sources.items()}
raw = read("efb9330c1",source_path.replace("prepare.py","algebraic/optimized/results/field31_s5_base0/public.json"))
assert hashlib.sha256(raw).hexdigest() == "a5fd508b6deacd2e2036a790946d7700929a822caf92e1fed699e6a7657fb9ca"
manifest = json.loads(raw)
p = 2**31-1
for depth in (1,2,5,8,10):
    for limit in (0,1,2**depth-1,2**depth):
        assert modules["layer"]["chain"](p,depth,root_limit=limit) == modules["scalar"]["chain"](p,depth,root_limit=limit)
assert modules["layer"]["chain"](2**61-1,6) == modules["scalar"]["chain"](2**61-1,6)
words = C.c_uint32 * 32
fn = C.CDLL(str(Path(sys.argv[1]).resolve())).m31_lift32
fn.argtypes = [C.POINTER(C.c_uint32)]*2
fn.restype = None
def lift(xs):
    points = []
    for i in range(0,len(xs),32):
        part = xs[i:i+32]
        ys = words()
        fn(words(*part),ys)
        points.extend((x,y) for x,y in zip(part,ys) if y != p)
    return points

writer = csv.writer(sys.stdout,lineterminator="\n")
writer.writerow(("depth","block","arm","calls","wall_ns","cpu_ns"))
long_blocks = sys.argv[2:] == ["--long"]
if sys.argv[2:] and not long_blocks:
    raise SystemExit("expected optional --long")
schedule = ((5,400),(8,128),(10,48),(12,12)) if long_blocks else ((5,48),(8,12),(10,4),(12,2))
for depth,calls in schedule:
    aux,xs = modules["scalar"]["chain"](p,depth,enumerate_all=True)
    points = []
    for x in xs:
        rhs = (x**3+2*x+14)%p
        y = pow(rhs,(p+1)//4,p)
        if y*y%p == rhs:
            points.append((x,min(y,p-y)))
        for m in aux["maps"]:
            u = (x-m["r"])%p
            x = (u+m["A"]+m["B"]*pow(u,-1,p))%p
        assert x == aux["terminal_c"]
    assert points == lift(xs)
    if depth == 5:
        assert xs == manifest["structured_roots"] and sorted(map(list,points)) == manifest["factor_base"]
    for block in range(24 if long_blocks else 16):
        for arm in (("scalar","layer") if block%2 == 0 else ("layer","scalar")):
            chain = modules[arm]["chain"]
            w,c = perf_counter_ns(),process_time_ns()
            for _ in range(calls):
                info,roots = chain(p,depth,enumerate_all=True)
                result = lift(roots)
            ct,wt = process_time_ns()-c,perf_counter_ns()-w
            assert info == aux and roots == xs and result == points
            writer.writerow((depth,block,arm,calls,wt,ct))
