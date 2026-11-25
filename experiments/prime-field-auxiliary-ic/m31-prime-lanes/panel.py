import contextlib
import csv
import ctypes as C
import os
import runpy
import sys
from time import perf_counter_ns, process_time_ns

with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink):
    panel=runpy.run_path("m31-projective-kernel/panel.py")
r=panel["replay"]
r.chain["chain"]=panel["candidate"]
setup=panel["setup"]["compact_setup"]
expected=panel["setup"]["expected"]
xs=panel["setup"]["fixture"]["roots"]
hits=panel["setup"]["smooth"]
control=r.baseline["fn"]
candidate=C.CDLL(sys.argv[4]).m31_prime_lanes
candidate.argtypes,candidate.restype=control.argtypes,control.restype
words=r.word*len(xs)
source=words(*xs)
for scope in ("check", "filter", "setup"):
    if scope=="check":
        values=r.baseline["tests"]
        tests=[*values,*(r.p-x for x in values if x),0,1,r.p-1]
        fixture=panel["setup"]["fixture"]
        oracle=[x for x in tests if x and fixture["trial"](min(x,r.p-x))]
        buf=(r.word*len(tests))(*tests)
        assert buf[:candidate(buf,len(buf))]==oracle
        assert candidate(buf,0)==0
        writer=csv.writer(sys.stdout)
        writer.writerow(("scope","block","arm","wall_ns","cpu_ns"))
        continue
    for block in range(-8,96):
        arms=[("coordinate",control),("prime",candidate)]
        for name,fn in arms[::1 if block%2==0 else -1]:
            r.baseline["fn"]=fn
            if scope=="filter": buf=words.from_buffer_copy(source)
            cpu,wall=process_time_ns(),perf_counter_ns()
            result=fn(buf,len(buf)) if scope=="filter" else setup()
            wall,cpu=perf_counter_ns()-wall,process_time_ns()-cpu
            assert (buf[:result]==hits if scope=="filter" else result==expected)
            if block>=0:
                writer.writerow((scope,block,name,wall,cpu))
