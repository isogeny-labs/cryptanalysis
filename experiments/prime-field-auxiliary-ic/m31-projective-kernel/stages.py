"""Measure only the 15 frozen kernel requests with one ctypes call per stage."""
import contextlib
import csv
import ctypes as C
import os
import runpy
import sys
from itertools import permutations
from time import perf_counter_ns

with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink):
    panel = runpy.run_path("m31-projective-kernel/panel.py")
calls, expected = [], []
def capture(curve, point, count):
    calls.append((*point, curve.a2, curve.a4, count))
    x = panel["kernel_x"](curve, point, count)
    expected.append(x)
    return x

panel["candidate"].__globals__["kernel_x"] = capture
panel["candidate"](panel["replay"].p, 15)
assert len(calls) == 15 and sum(row[-1] for row in calls) == 105
projective_calls = [(x,a,b,count) for x,y,a,b,count in calls]
arms = dict(projective=(panel["kernel"],projective_calls))
for name in ("power","euclid"):
    fn = getattr(panel["lib"],"m31_affine_"+name)
    fn.argtypes,fn.restype = [C.c_uint32]*5,C.c_uint32
    arms[name] = (fn,calls)
writer = csv.writer(sys.stdout)
writer.writerow(("block","arm","total_ns","repetitions"))
orders = list(permutations(arms))
for block in range(-6,96):
    for name in orders[block%6]:
        fn,inputs = arms[name]
        start = perf_counter_ns()
        for _ in range(32):
            result = [fn(*args) for args in inputs]
        elapsed = perf_counter_ns()-start
        assert result == expected
        if block>=0:
            writer.writerow((block,name,elapsed,32))
