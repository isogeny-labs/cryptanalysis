"""Run with python3 replay.py on Linux or macOS. Requires a C99 compiler."""

import ctypes
import hashlib
import os
import platform
import random
import shlex
import statistics
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

P = 2**31 - 1
WORD = ctypes.c_uint32
POINTER = ctypes.POINTER(WORD)
CANARY = 0xBAD0CAFE


def reference(x):
    rhs = (x**3 + 2*x + 14) % P
    y = pow(rhs, (P+1)//4, P)
    return min(y, P-y) if y*y % P == rhs else P


def build(directory, name, compiler):
    library = directory / (name + ".so")
    flags = ["-dynamiclib"] if sys.platform == "darwin" else ["-shared", "-fPIC"]
    if name == "remainder":
        flags.append("-DUSE_REMAINDER")
    source = Path(__file__).with_name("lift.c")
    subprocess.run([*compiler, "-O3", "-std=c99", *flags, str(source), "-o", str(library)],
                   check=True)
    lift = ctypes.CDLL(str(library)).lift_batch
    lift.argtypes = [POINTER, POINTER, ctypes.c_size_t]
    lift.restype = None
    return lift


def run(lift, xs):
    # Keep guards before and after the writable region, including empty batches.
    size = len(xs)
    inputs = (WORD * size)(*xs)
    output = (WORD * (size+2))(*([CANARY] * (size+2)))
    interior = ctypes.cast(ctypes.byref(output, ctypes.sizeof(WORD)), POINTER)
    lift(inputs, interior, size)
    if output[0] != CANARY or output[-1] != CANARY:
        raise ValueError(f"output guard overwritten at batch size {size}")
    return output[1:-1]


def main():
    rng = random.Random(11242026)
    xs = [0, 1, 2, 3, P-3, P-2, P-1]
    xs.extend(rng.randrange(P) for _ in range(32768))
    expected = [reference(x) for x in xs]
    compiler = shlex.split(os.environ.get("CC", "cc"))
    print(platform.machine(), subprocess.check_output([*compiler, "--version"],
          text=True).splitlines()[0])
    with tempfile.TemporaryDirectory() as tmp:
        kernels = {name: build(Path(tmp), name, compiler) for name in ("fold", "remainder")}
        for name, kernel in kernels.items():
            for width in (0, 1, 3, 4, 7, 8, 15, 16, 31, 32, 33, len(xs)):
                if run(kernel, xs[:width]) != expected[:width]:
                    raise ValueError(f"{name} disagrees with reference at width {width}")
        # Time complete 32-coordinate calls, including marshalling and guards.
        blocks = [xs[i:i+32] for i in range(0, len(xs), 32)]
        methods = {"python": lambda block: [reference(x) for x in block]}
        for name, kernel in kernels.items():
            methods[name] = lambda block, k=kernel: run(k, block)
        samples = {name: [] for name in methods}
        order = list(methods)
        for _ in range(9):
            rng.shuffle(order)
            for name in order:
                start = time.perf_counter_ns()
                values = [y for block in blocks for y in methods[name](block)]
                samples[name].append((time.perf_counter_ns()-start)/len(xs))
                if values != expected:
                    raise ValueError(f"{name} disagrees with reference in batched replay")
        for name, times in samples.items():
            print(f"{name}: {statistics.median(times):.1f} ns/input")
    digest = hashlib.sha256(b"".join(struct.pack("<I", y) for y in expected)).hexdigest()
    print(f"{len(xs)} inputs, {expected.count(P)} rejected, output SHA-256 {digest}")


if __name__ == "__main__":
    main()
