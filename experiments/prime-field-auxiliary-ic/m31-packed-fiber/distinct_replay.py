"""Use the four packed-replay library arguments followed by the distinct library."""
from array import array
import csv
import ctypes as C
from pathlib import Path
import subprocess
import sys
from time import perf_counter_ns, process_time_ns

import replay

if not __debug__:
    raise RuntimeError("validation requires Python assertions")

native = C.CDLL(sys.argv[5]).m31_distinct_fiber
native.argtypes = replay.fiber["lib"].m31_fiber.argtypes
native.restype = C.c_int


def distinct_fiber(roots, maps, terminal, modulus):
    assert modulus == replay.p
    scratch = (replay.word * len(roots)).from_buffer_copy(roots)
    steps = replay.fiber["buffer"](step[k] for step in maps for k in ("r", "A", "B"))
    return bool(native(scratch, len(roots), steps, len(maps), terminal))


# Produce a controlled variant of the frozen chain. Only a complete, natively
# checked half-walk may use the sibling certificate in place of the set.
path = "experiments/prime-field-auxiliary-ic/snapshot/prepare.py"
source = subprocess.check_output(["git", "show", f"e7454b777:{path}"],
                                 cwd=Path(__file__).resolve().parent, text=True)
start = source.index("def chain(")
body = source[start:source.index("\ndef ", start + 4)]
check = "    assert len(set(V)) == len(V)"
assert body.count(check) == 1
body = body.replace(check, "    if not (paired and s >= 8):\n    " + check)
candidate_env = dict(replay.chain, _check_sibling_fiber=distinct_fiber)
exec(compile(body, path, "exec"), candidate_env)
control = replay.chain["chain"]
candidate = candidate_env["chain"]
for depth in (8, 10, 12, 15):
    info, xs = control(replay.p, depth)
    metadata, ys = candidate(replay.p, depth)
    assert metadata == info and xs == ys
    for index in (0, len(xs)//2, len(xs)-1):
        damaged = ys[:]
        damaged[index] = (damaged[index] + 1) % replay.p
        assert not distinct_fiber(damaged, info["maps"], info["terminal_c"], replay.p)

duplicate = array("I", [2, 2])
maps = [dict(r=0, A=0, B=4)]
assert replay.check_fiber(duplicate, maps, 4, replay.p)
assert not distinct_fiber(duplicate, maps, 4, replay.p)

writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(("block", "path", "cpu_ns", "wall_ns"))
arms = [("packed", control), ("distinct", candidate)]
for block in range(64):
    for name, chain in (arms if block % 2 == 0 else reversed(arms)):
        replay.chain["chain"] = chain
        cpu, wall = process_time_ns(), perf_counter_ns()
        points = replay.packed_setup()
        cpu, wall = process_time_ns() - cpu, perf_counter_ns() - wall
        assert points == replay.baseline["fixture"]["reference"]
        writer.writerow((block, name, cpu, wall))
