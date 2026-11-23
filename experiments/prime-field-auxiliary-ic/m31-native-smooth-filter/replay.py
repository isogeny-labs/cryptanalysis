import csv
import ctypes as C
from pathlib import Path
import random
import runpy
import sys
from time import perf_counter_ns, process_time_ns

here=Path(__file__).resolve().parent
prev=runpy.run_path(str(here.parent/"m31-native-fiber/replay.py"))
fixture,ns=prev["fixture"],prev["ns"]
ns["_append_reciprocals"],ns["_check_sibling_fiber"]=prev["reciprocals"],prev["fiber"]
p=prev["p"]
fn=C.CDLL(sys.argv[4]).m31_smooth211
fn.argtypes=[prev["ptr"],C.c_size_t]
fn.restype=C.c_size_t

def filtered(xs):
    values=prev["buffer"](xs)
    return values[:fn(values,len(xs))]

def check(xs):
    reference=[x for x in xs if x and fixture["trial"](min(x,p-x))]
    assert filtered(xs)==reference

rng=random.Random(211)
tests=list(range(8193))+[rng.randrange(p) for _ in range(8192)]
for q in [*fixture["primes"],223,227]:
    power=q
    while power<=p//2:
        tests.extend((power-1,power,power+1))
        power*=q
check(tests+[p-x for x in tests if x])
check(fixture["roots"])
assert filtered([])==[]

def candidate():
    roots=ns["chain"](p,15,enumerate_all=True)[1]
    return fixture["lift"](filtered(roots))

if __name__=="__main__":
    writer=csv.writer(sys.stdout,lineterminator="\n")
    writer.writerow(("block","arm","wall_ns","cpu_ns"))
    for block in range(32):
        arms=(("divisor",lambda:fixture["run"]("filter_divisor")),("native",candidate))
        for name,f in (arms if block%2==0 else reversed(arms)):
            wall,cpu=perf_counter_ns(),process_time_ns()
            pts=f()
            ct,wt=process_time_ns()-cpu,perf_counter_ns()-wall
            assert pts==fixture["reference"]
            writer.writerow((block,name,wt,ct))
