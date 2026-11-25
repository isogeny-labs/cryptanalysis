"""Run python3 replay.py on macOS or Linux with a C++17 compiler."""
import ctypes as ct
from collections import Counter
import os
from pathlib import Path
import random
import shlex
import statistics
import subprocess
import sys
import tempfile
import time

U32 = ct.c_uint32
U64 = ct.c_uint64


def reference(keys):
    counts = Counter(keys)
    return sorted((i for i, key in enumerate(keys) if counts[key] > 1),
                  key=lambda i: (keys[i], i))


def compare(group, keys, rounds):
    want = reference(keys)
    inputs = (U64 * len(keys))(*keys)
    samples = [[], []]
    for repeat in range(rounds):
        for mode in (repeat % 2, 1 - repeat % 2):
            start = time.perf_counter_ns()
            output = (U32 * (len(keys) + 1))()
            output[len(keys)] = 0xBAADF00D
            count = group(inputs, len(keys), output, mode)
            samples[mode].append((time.perf_counter_ns() - start) / 1e6)
            if count != len(want) or output[:count] != want or output[-1] != 0xBAADF00D:
                raise ValueError(f"incorrect result for n={len(keys)}, mode={mode}")
    return [statistics.median(times) for times in samples]


def main():
    with tempfile.TemporaryDirectory() as tmp:
        lib = Path(tmp) / 'groups.so'
        flags = ['-dynamiclib'] if sys.platform == 'darwin' else ['-fPIC', '-shared']
        subprocess.run([*shlex.split(os.getenv('CXX', 'c++')), '-std=c++17', '-O3',
                        *flags, str(Path(__file__).with_name('groups.cpp')), '-o', str(lib)],
                       check=True)
        group = ct.CDLL(str(lib)).group_indices
        group.argtypes = [ct.POINTER(U64), U32, ct.POINTER(U32), ct.c_uint]
        group.restype = ct.c_int64
        for keys in ([], [7], [3] * 513, [0, 2**64-1, 0, 9, 2**64-1],
                     [i << 51 for i in range(1000)]):
            compare(group, keys, 2)
        rng = random.Random(261124)
        print("length,radix_ms,filter_ms")
        for n in (128, 4096, 32768, 148240, 295936, 524288, 1048576):
            keys = [rng.getrandbits(62) for _ in range(n)]
            for i in range(1, n, 3571):
                keys[i] = keys[i-1]
            radix, filtered = compare(group, keys, 16)
            print(f"{n},{radix:.4f},{filtered:.4f}")


if __name__ == '__main__':
    main()
