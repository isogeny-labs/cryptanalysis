"""Compare the two layer implementations inside the same public setup."""
from pathlib import Path
import ctypes as C
import csv
import subprocess
import sys
from time import perf_counter_ns, process_time_ns

here=Path(__file__).resolve().parent
# Load the checked fixture, reference implementation and FFI lifting code from
# the prior benchmark without running its four-arm panel.
prior=here.parent/"m31-smooth-basis-setup/bench.py"
fixture=dict(__file__=str(prior))
exec(compile(prior.read_text().split('arms=["lift_trial"')[0],str(prior),"exec"),fixture)
ns=fixture["ns"]
reference=ns["_layer_walk"]
translate=C.CDLL(sys.argv[2]).m31_translate
translate.argtypes=[C.c_size_t]+[C.POINTER(C.c_uint32)]*3+[C.c_uint32]*2
translate.restype=C.c_int

def native(curve,start,generator,count):
    assert curve.p==2**31-1 and curve.a2==0 and count>0 and count&(count-1)==0
    xs=(C.c_uint32*count)()
    ys=(C.c_uint32*count)()
    prefix=(C.c_uint32*(count//2))()
    xs[0],ys[0]=start
    stride=generator
    n=1
    while n<count:
        if not translate(n,xs,ys,prefix,*stride):
            raise ValueError("exceptional affine denominator")
        n*=2
        if n<count:stride=curve.add(stride,stride)
    return list(xs),curve.add((xs[-1],ys[-1]),generator)

for depth in (8,10,12,15):
    ns["_layer_walk"]=reference
    expected=ns["chain"](2**31-1,depth)
    ns["_layer_walk"]=native
    assert ns["chain"](2**31-1,depth)==expected

writer=csv.writer(sys.stdout,lineterminator="\n")
writer.writerow(("block","arm","wall_ns","cpu_ns"))
for block in range(32):
    order=(("python",reference),("native",native))
    for arm,fn in (order if block%2==0 else reversed(order)):
        ns["_layer_walk"]=fn
        wall,cpu=perf_counter_ns(),process_time_ns()
        pts=fixture["run"]("filter_divisor")
        ct,wt=process_time_ns()-cpu,perf_counter_ns()-wall
        assert pts==fixture["reference"]
        writer.writerow((block,arm,wt,ct))
