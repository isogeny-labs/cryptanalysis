import contextlib
import csv
import ctypes as C
import os
import runpy
import sys
from time import perf_counter_ns, process_time_ns

with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink):
    setup = runpy.run_path("m31-packed-lift/panel.py")
ctx, replay = setup["ctx"], setup["r"]
lib = C.CDLL(sys.argv[5])
check = ctx["distinct_fiber"].__globals__
batched = lib.m31_batched_fiber
batched.argtypes, batched.restype = check["native"].argtypes, C.c_int
check["native"] = batched
kernel = lib.m31_kernel_x
kernel.argtypes, kernel.restype = [C.c_uint32]*4, C.c_uint32

def kernel_x(curve, point, count):
    assert point is not None and curve.a6 == 0 and curve.p == replay.p
    value = kernel(point[0], curve.a2, curve.a4, count)
    assert value < replay.p
    return value

original = ctx["candidate"]
old = """        K = current.double_n(H, s-j-1)
        assert K is not None and K[1] == 0
        r = K[0]"""
assert ctx["body"].count(old) == 1
env = dict(original.__globals__, kernel_x=kernel_x)
exec(compile(ctx["body"].replace(old, "        r = kernel_x(current, H, s-j-1)"),
             "<projective kernel replay>", "exec"), env)
candidate = env["chain"]
for depth in (8, 9, 10, 12, 15, 17):
    assert original(replay.p, depth) == candidate(replay.p, depth)

# Compare both finite order-two points and rejection paths on several models.
for a,b in ((0,1), (6,8), (replay.p-3,2)):
    curve = env["Curve"](replay.p, a2=a, a4=b)
    for start in (0,1,2,3,7,19,101):
        point = curve.point(start)
        for exponent in range(32):
            k = curve.double_n(point, exponent)
            expected = k[0] if k is not None and k[1] == 0 else replay.p
            assert kernel(point[0],a,b,exponent) == expected

writer = csv.writer(sys.stdout)
writer.writerow(("block","arm","wall_ns","cpu_ns"))
for block in range(-8,128):
    arms = [("affine",original), ("projective",candidate)]
    for name,fn in arms[::1 if block%2 == 0 else -1]:
        replay.chain["chain"] = fn
        cpu,wall = process_time_ns(),perf_counter_ns()
        result = setup["compact_setup"]()
        wall,cpu = perf_counter_ns()-wall,process_time_ns()-cpu
        assert result == setup["expected"]
        if block >= 0:
            writer.writerow((block,name,wall,cpu))
