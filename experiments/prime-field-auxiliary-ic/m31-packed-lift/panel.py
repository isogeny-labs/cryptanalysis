import contextlib
import csv
import ctypes as C
import os
from pathlib import Path
import runpy
import sys
from time import perf_counter_ns, process_time_ns

packed = Path("m31-packed-fiber").resolve()
sys.path.insert(0, str(packed))
with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink):
    ctx = runpy.run_path(str(packed / "distinct_replay.py"))
r = ctx["replay"]
r.chain["chain"] = ctx["candidate"]
fixture = r.baseline["fixture"]
word = r.word
ptr = C.POINTER(word)
native = C.CDLL(sys.argv[1]).m31_lift_points
native.argtypes = [ptr, C.c_size_t, ptr, ptr]
native.restype = C.c_size_t

def compact(xs, n):
    words = word * n
    px, py = words(), words()
    count = native(xs, n, px, py)
    return list(zip(px[:count], py[:count], strict=True))

def compact_setup():
    _, roots = r.chain["chain"](r.p, 15, enumerate_all=True)
    xs = (word * len(roots)).from_buffer(roots)
    size = r.baseline["fn"](xs, len(roots))
    return compact(xs, size)

smooth = [x for x in fixture["roots"] if fixture["trial"](min(x, r.p-x))]
xs = (word * len(smooth))(*smooth)
expected = fixture["reference"]
assert len(smooth) == 392 and len(expected) == 195
for n in range(65):
    # Include repeats and the empty and partial final block.
    test = ([3, 3, 0, r.p-1] + smooth[:61])[:n]
    assert compact((word*n)(*test), n) == fixture["lift"](test)

arms = {
    "lift": (lambda: fixture["lift"](xs[:]), lambda: compact(xs, len(xs))),
    "setup": (r.packed_setup, compact_setup),
}
writer = csv.writer(sys.stdout)
writer.writerow(("scope", "block", "arm", "wall_ns", "cpu_ns"))
for scope, functions in arms.items():
    for block in range(-8, 128):
        for arm in ((0, 1) if block%2 == 0 else (1, 0)):
            cpu, wall = process_time_ns(), perf_counter_ns()
            points = functions[arm]()
            wall, cpu = perf_counter_ns()-wall, process_time_ns()-cpu
            assert points == expected
            if block >= 0:
                writer.writerow((scope, block, arm, wall, cpu))
