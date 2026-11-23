"""Charge the entire frozen basis setup for each kernel choice."""
import contextlib
import csv
import ctypes as C
from itertools import permutations
import os
import random
import runpy
import sys
from time import perf_counter_ns, process_time_ns

with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink):
    panel = runpy.run_path("m31-projective-kernel/panel.py")
kernel_env = panel["candidate"].__globals__
projective = kernel_env["kernel_x"]
p = panel["replay"].p

def affine(fn):
    fn.argtypes, fn.restype = [C.c_uint32]*5, C.c_uint32
    for a,b in ((0,1), (6,8), (p-3,2)):
        curve = kernel_env["Curve"](p,a2=a,a4=b)
        for start in (0,1,2,3,7,19,101):
            x,y = curve.point(start)
            for exponent in range(32):
                k = curve.double_n((x,y),exponent)
                assert fn(x,y,a,b,exponent) == (k[0] if k and k[1]==0 else p)

    def invoke(curve, point, count):
        assert point is not None and curve.a6 == 0 and curve.p == p
        value = fn(*point, curve.a2, curve.a4, count)
        assert value < p
        return value
    return invoke

arms = dict(python=None, power=affine(panel["lib"].m31_affine_power),
            euclid=affine(panel["lib"].m31_affine_euclid), projective=projective)
replay = panel["replay"]
for depth in (8, 9, 10, 12, 15, 17):
    reference = panel["original"](p, depth)
    for fn in list(arms.values())[1:]:
        kernel_env["kernel_x"] = fn
        assert panel["candidate"](p, depth) == reference
writer = csv.writer(sys.stdout)
writer.writerow(("block","arm","wall_ns","cpu_ns"))
orders = list(permutations(arms))
rng = random.Random(31)
for repeat in range(5):
    rng.shuffle(orders)
    for idx,order in enumerate(orders):
        for name in order:
            kernel_env["kernel_x"] = arms[name]
            replay.chain["chain"] = panel["original" if name=="python" else "candidate"]
            cpu,wall = process_time_ns(),perf_counter_ns()
            result = panel["setup"]["compact_setup"]()
            wall,cpu = perf_counter_ns()-wall,process_time_ns()-cpu
            assert result == panel["setup"]["expected"]
            if repeat:
                writer.writerow(((repeat-1)*24+idx,name,wall,cpu))
