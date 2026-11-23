from array import array
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
check = ctx["distinct_fiber"]
env = check.__globals__
control = env["native"]
candidate = C.CDLL(sys.argv[5]).m31_batched_fiber
candidate.argtypes, candidate.restype = control.argtypes, control.restype
info, roots = ctx["candidate"](replay.p, 15)
maps, terminal = info["maps"], info["terminal_c"]

def validate(values, steps, end, expected):
    for kernel in (control, candidate):
        env["native"] = kernel
        assert check(values, steps, end, replay.p) == expected

validate(roots, maps, terminal, True)
for i in [0, 1, 15, 16, len(roots)//2-1, len(roots)//2, len(roots)-1]:
    for value in ((roots[i]+1)%replay.p, replay.p, 2**32-1):
        damaged = roots[:]
        damaged[i] = value
        validate(damaged, maps, terminal, False)
for i in range(len(maps)):
    for key in ("r", "A", "B"):
        damaged = [dict(row) for row in maps]
        damaged[i][key] = replay.p
        validate(roots, damaged, terminal, False)
validate(array("I", [2,2]), [dict(r=0,A=0,B=4)], 4, False)
validate(array("I", [0]), [], 0, True)
validate(array("I", [replay.p]), [], replay.p, False)
validate(array("I"), [], 0, False)
validate(roots[:-1], maps, terminal, False)
validate(roots, maps, (terminal+1)%replay.p, False)

writer = csv.writer(sys.stdout)
writer.writerow(("scope","block","arm","wall_ns","cpu_ns"))
for scope in ("validation","setup"):
    for block in range(-8,128):
        arms = [("control", control), ("batched", candidate)]
        for name,kernel in arms[::1 if block%2 == 0 else -1]:
            env["native"] = kernel
            cpu, wall = process_time_ns(), perf_counter_ns()
            result = check(roots,maps,terminal,replay.p) if scope=="validation" else setup["compact_setup"]()
            wall, cpu = perf_counter_ns()-wall, process_time_ns()-cpu
            assert result == (True if scope=="validation" else setup["expected"])
            if block >= 0:
                writer.writerow((scope,block,name,wall,cpu))
