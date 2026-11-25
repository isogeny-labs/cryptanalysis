"""Run with python3 replay-neon-inverse.py on AArch64 with clang++.

Times are for contiguous, already-packed independent field elements.
The CSV records individual calls in balanced order, including FFI overhead.
"""
import csv
import ctypes
import itertools
import platform
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path

P = 2**31 - 1
MODES = {8: "portable8", 16: "neon8", 32: "neon16"}
WORD = ctypes.c_uint32


def replay(kernel):
    orders = list(itertools.permutations(MODES))
    writer = csv.writer(sys.stdout)
    writer.writerow(["seed", "elements", "implementation", "elapsed_ns"])
    sizes = [*range(34), 1023, 1024, 1025, 2049] + [148240] * 48
    for seed, count in enumerate(sizes):
        rng = random.Random(seed)
        values = [rng.randrange(1, P) for _ in range(count)]
        for i, edge in enumerate((1, P - 1, 2, P - 2, 1 << 30)[:count]):
            values[i] = edge
        inputs = (WORD * count)(*values)
        for mode in orders[seed % len(orders)]:
            guard = 0xDEADBEEF
            output = (WORD * (count + 2))()
            output[0] = output[-1] = guard
            pointer = ctypes.cast(ctypes.byref(output, ctypes.sizeof(WORD)),
                                  ctypes.POINTER(WORD))
            start = time.perf_counter_ns()
            kernel(inputs, pointer, count, mode)
            elapsed = time.perf_counter_ns() - start
            if output[0] != guard or output[-1] != guard:
                raise ValueError(f"output guard overwritten at seed {seed}, mode {mode}")
            for index, value in enumerate(values, 1):
                inverse = output[index]
                if inverse >= P or inverse * value % P != 1:
                    raise ValueError(f"incorrect inverse at seed {seed}, index {index}, mode {mode}")
            writer.writerow([seed, count, MODES[mode], elapsed])


if __name__ == "__main__":
    if platform.machine().lower() not in {"aarch64", "arm64"}:
        sys.exit("This benchmark requires native AArch64.")
    with tempfile.TemporaryDirectory() as scratch:
        library = Path(scratch) / "neon-inverse.so"
        source = Path(__file__).with_name("neon-inverse.cpp")
        subprocess.run(["clang++", "-std=c++17", "-O3", "-shared", "-fPIC",
                        str(source), "-o", str(library)], check=True)
        kernel = ctypes.CDLL(str(library)).compare_panel
        kernel.argtypes = [ctypes.POINTER(WORD), ctypes.POINTER(WORD),
                           ctypes.c_size_t, ctypes.c_int]
        kernel.restype = None
        replay(kernel)
