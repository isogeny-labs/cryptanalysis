"""Run with the four library paths documented in ../m31-native-smooth-filter."""
import csv
import ctypes as C
import runpy
import sys
from array import array
from pathlib import Path
from time import perf_counter_ns, process_time_ns

baseline = runpy.run_path(str(Path(__file__).resolve().parents[1] / "m31-native-smooth-filter/replay.py"))
fiber = baseline["prev"]
chain = baseline["ns"]
word = C.c_uint32
p = 2**31 - 1
assert array("I").itemsize == C.sizeof(word)


def packed_layer(curve, start, generator, count):
    assert curve.p == p and curve.a2 == 0 and count > 0 and count & (count - 1) == 0
    xs, ys = (word * count)(), (word * count)()
    scratch = (word * (count // 2))()
    xs[0], ys[0] = start
    width = 1
    stride = generator
    while width < count:
        if not fiber["ref"]["translate"](width, xs, ys, scratch, *stride):
            raise ValueError("exceptional affine denominator")
        width *= 2
        if width < count:
            stride = curve.add(stride, stride)
    roots = array("I")
    roots.frombytes(memoryview(xs).cast("B"))
    return roots, curve.add((xs[-1], ys[-1]), generator)


def append_reciprocals(roots, modulus):
    assert modulus == p
    words = word * len(roots)
    tail = words()
    if not fiber["lib"].m31_reciprocals(words.from_buffer(roots), tail, len(roots)):
        raise ValueError("zero has no field inverse")
    roots.frombytes(memoryview(tail).cast("B"))


def check_fiber(roots, maps, terminal, modulus):
    assert modulus == p
    steps = fiber["buffer"](step[key] for step in maps for key in ("r", "A", "B"))
    scratch = (word * len(roots)).from_buffer_copy(roots)
    return bool(fiber["lib"].m31_fiber(scratch, len(roots), steps, len(maps), terminal))


packed = dict(_layer_walk=packed_layer, _append_reciprocals=append_reciprocals,
              _check_sibling_fiber=check_fiber)
original = {key: chain[key] for key in packed}
for depth in (8, 10, 12, 15):
    chain.update(original)
    info, expected = chain["chain"](p, depth)
    chain.update(packed)
    metadata, roots = chain["chain"](p, depth)
    assert metadata == info and list(roots) == expected
    for index in (0, len(roots) // 2, len(roots) - 1):
        damaged = roots[:]
        damaged[index] = (damaged[index] + 1) % p
        assert not check_fiber(damaged, info["maps"], info["terminal_c"], p)


def packed_setup():
    _, roots = chain["chain"](p, 15, enumerate_all=True)
    values = (word * len(roots)).from_buffer(roots)
    size = baseline["fn"](values, len(roots))
    return baseline["fixture"]["lift"](values[:size])


if __name__ == "__main__":
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(("block", "path", "cpu_ns", "wall_ns"))
    arms = [("baseline", original, baseline["candidate"]), ("packed", packed, packed_setup)]
    for block in range(48):
        for name, hooks, setup in (arms if block % 2 == 0 else reversed(arms)):
            chain.update(hooks)
            cpu, wall = process_time_ns(), perf_counter_ns()
            points = setup()
            cpu, wall = process_time_ns() - cpu, perf_counter_ns() - wall
            assert points == baseline["fixture"]["reference"]
            writer.writerow((block, name, cpu, wall))
