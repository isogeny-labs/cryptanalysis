"""Time checked, setup-charged public basis construction on the frozen M31 input."""
import csv
import ctypes as C
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter_ns, process_time_ns

here = Path(__file__).resolve().parent
src = "experiments/prime-field-auxiliary-ic/snapshot"
def read(path):
    return subprocess.check_output(["git","show",f"e7454b777:{src}/{path}"],cwd=here)
ns = dict(__name__="archived_curve",__file__="prepare.py")
exec(compile(read("prepare.py"),"prepare.py","exec"),ns)
p=2**31-1
primes=[q for q in range(2,212) if all(q%d for d in range(2,int(q**0.5)+1))]
def make_multiple():
    result=1
    for q in primes:
        power=q
        while power <= (p//2)//q:
            power*=q
        result*=power
    return result

def trial(x):
    for q in primes:
        while x%q==0:
            x//=q
        if x==1: return True
    return False

words=C.c_uint32*32
native=C.CDLL(sys.argv[1]).m31_lift32
native.argtypes=[C.POINTER(C.c_uint32)]*2
native.restype=None
def lift(xs):
    out=[]
    for i in range(0,len(xs),32):
        part=xs[i:i+32]
        ys=words()
        native(words(*part),ys)
        out.extend((x,y) for x,y in zip(part,ys) if y!=p)
    return out

def run(arm):
    roots=ns["chain"](p,15,enumerate_all=True)[1]
    if arm.endswith("divisor"):
        multiple=make_multiple()
        test=lambda x:multiple%x==0
    else:
        test=trial
    if arm.startswith("filter"):
        return lift([x for x in roots if test(min(x,p-x))])
    return [(x,y) for x,y in lift(roots) if test(min(x,p-x))]

roots=json.loads(read("algebraic/structure_results/field31_s15/structured_roots.json"))
assert len(roots)==len(set(roots))==32768 and 0 not in roots
multiple=make_multiple()
assert all(trial(min(x,p-x))==(multiple%min(x,p-x)==0) for x in roots)
reference=[]
for x in roots:
    if trial(min(x,p-x)):
        rhs=(x**3+2*x+14)%p
        y=pow(rhs,(p+1)//4,p)
        if y*y%p==rhs:reference.append((x,min(y,p-y)))
assert len(reference)==195
arms=["lift_trial","filter_trial","filter_divisor","lift_divisor"]
writer=csv.writer(sys.stdout,lineterminator="\n")
writer.writerow(("block","arm","wall_ns","cpu_ns"))
for block in range(24):
    # Balanced Latin square: equal order and carry-over counts per four blocks.
    order=[arms[(i+block)%4] for i in (0,1,3,2)]
    for arm in order:
        wall,cpu=perf_counter_ns(),process_time_ns()
        result=run(arm)
        ct,wt=process_time_ns()-cpu,perf_counter_ns()-wall
        assert result==reference
        writer.writerow((block,arm,wt,ct))
