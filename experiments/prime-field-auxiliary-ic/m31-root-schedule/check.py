"""Exercise the C ABI on native and forced-portable builds."""
import ctypes as c
from pathlib import Path
from random import Random
import subprocess
import tempfile

here = Path(__file__).resolve().parent
p = 2**31 - 1
rng = Random(20261122)
word = c.c_uint32
ptr = c.POINTER(word)
with tempfile.TemporaryDirectory() as tmp:
    subprocess.run(["cc", "-std=c11", "-I", here, "-x", "c", "-fsyntax-only", "-"],
                   input='#include "root.h"\n', text=True, check=True)
    for mode in ("native", "portable"):
        path = Path(tmp) / (mode + ".so")
        flags = ["-DM31_ROOT_PORTABLE"] if mode == "portable" else []
        subprocess.run(["c++", "-std=c++17", "-O3", "-shared", "-fPIC", *flags,
                        here / "root.cpp", "-o", path], check=True)
        roots = c.CDLL(str(path)).m31_checked_roots
        roots.argtypes = (ptr, ptr, c.c_size_t)
        roots.restype = None
        roots(None, None, 0)
        for size in [*range(100), 255, 256, 257, 4095, 4096, 4097]:
            xs = [rng.randrange(p) for _ in range(size)]
            for i, x in enumerate([0, 1, 2, p-2, p-1][:size]):
                xs[i] = x
            ys = [pow(x, 2**29, p) for x in xs]
            expected = [min(y, p-y) if y*y % p == x else p for x, y in zip(xs, ys)]
            guard = 0xdeadbeef
            for inplace in (False, True):
                source = (word * (size+2))(guard, *xs, guard)
                dest = source if inplace else (word * (size+2))(guard, *([guard]*size), guard)
                roots(c.cast(c.byref(source, 4), ptr), c.cast(c.byref(dest, 4), ptr), size)
                assert list(dest) == [guard, *expected, guard]
                if not inplace:
                    assert list(source) == [guard, *xs, guard]
        print(mode, "passed")
