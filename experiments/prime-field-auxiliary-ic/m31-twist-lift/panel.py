"""Run through replay.sh with the frozen packed-setup dependencies."""
import contextlib
import csv
import ctypes as C
import os
from pathlib import Path
import runpy
import sys
from time import perf_counter_ns, process_time_ns

lib = C.CDLL(sys.argv.pop())
packed = Path("m31-packed-fiber").resolve()
sys.path.insert(0, str(packed))
with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink):
    ctx = runpy.run_path(str(packed / "distinct_replay.py"))
r = ctx["replay"]
r.chain["chain"] = ctx["candidate"]
fixture = r.baseline["fixture"]
p = r.p
xs = [x for x in fixture["roots"] if fixture["trial"](min(x, p-x))]

def oracle(x, constant):
    rhs = (x**3 + 2*x + constant) % p
    y = pow(rhs, (p+1)//4, p)
    return min(y, p-y) if y*y % p == rhs else p

def reference(values):
    return ([oracle(x, 14) for x in values], [oracle(-x % p, -14) for x in values])

def prepare(fn):
    fn.argtypes = [C.POINTER(r.word), C.c_size_t, C.POINTER(r.word), C.POINTER(r.word)]
    fn.restype = None
    def run(values):
        words = r.word * len(values)
        first, second = words(), words()
        fn(words(*values), len(values), first, second)
        return list(first), list(second)
    return run

expected = reference(xs)
assert len(xs) == 392 and all((a == p) != (b == p) for a,b in zip(*expected))
assert [(x,y) for x,y in zip(xs,expected[0]) if y != p] == fixture["reference"]
arms = [("separate", prepare(lib.separate)), ("shared", prepare(lib.shared))]
for _, fn in arms:
    for length in range(65):
        assert fn(xs[:length]) == reference(xs[:length])
writer = csv.writer(sys.stdout)
writer.writerow(("scope", "block", "arm", "wall_ns", "cpu_ns"))
words = r.word * len(xs)
packed_x, first, second = words(*xs), words(), words()
for scope in ("prepacked", "lift", "setup"):
    for block in range(-8, 128):
        for name, fn in arms[::1 if block % 2 == 0 else -1]:
            fixture["lift"] = fn
            native = getattr(lib, name)
            cpu, wall = process_time_ns(), perf_counter_ns()
            if scope == "prepacked":
                native(packed_x, len(xs), first, second)
            else:
                result = fn(xs) if scope == "lift" else r.packed_setup()
            wall, cpu = perf_counter_ns()-wall, process_time_ns()-cpu
            if scope == "prepacked":
                result = list(first), list(second)
            assert result == expected
            if block >= 0:
                writer.writerow((scope, block, name, wall, cpu))
