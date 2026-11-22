"""Check both shared libraries, then print paired elapsed times including ctypes."""
import ctypes as C
import random
import sys
from time import perf_counter_ns

P = 2**31 - 1
Word = C.c_uint32
Pointer = C.POINTER(Word)
rng = random.Random(314159)


def load(path):
    fn = C.CDLL(path).m31_batch_multiply
    fn.argtypes = [Pointer, Pointer, Pointer, C.c_size_t]
    fn.restype = None
    return fn


def guarded(words):
    array = (Word * (len(words) + 2))(123, *words, 456)
    return array, C.cast(C.byref(array, C.sizeof(Word)), Pointer)


functions = [load(path) for path in sys.argv[1:]]
assert len(functions) == 2
edges = [0, 1, P - 1, P, P + 1, 2 * P, 2**32 - 1]
for fn in functions:
    fn(None, None, None, 0)
    for n in [*range(66), 511, 512, 513, 65539]:
        a = [edges[i % 7] if i < 49 else rng.getrandbits(32) for i in range(n)]
        b = [edges[i // 7] if i < 49 else rng.getrandbits(32) for i in range(n)]
        for mode in ['separate', 'left', 'right', 'square', 'in-place square']:
            arrays = [guarded(seq) for seq in (a, b, [0]*n)]
            left, right, out = [ptr for _, ptr in arrays]
            if 'square' in mode:
                right = left
            if mode in ('left', 'in-place square'):
                out = left
            if mode == 'right':
                out = right
            fn(left, right, out, n)
            expected = [x*y % P for x, y in zip(a, a if 'square' in mode else b)]
            assert out[:n] == expected
            assert all((buf[0], buf[-1]) == (123, 456) for buf, _ in arrays)

print("length,round,portable_ns,native_ns,calls")
for n in [4, 17, 257, 4096, 65539]:
    buffers = [guarded([rng.getrandbits(32) for _ in range(n)]) for _ in range(3)]
    args = tuple(ptr for _, ptr in buffers) + (n,)
    calls = max(8, 131072 // n)
    for rep in range(-2, 24):
        elapsed = [0, 0]
        for arm in ((rep & 1), 1-(rep & 1)):
            fn = functions[arm]
            start = perf_counter_ns()
            for _ in range(calls):
                fn(*args)
            elapsed[arm] = perf_counter_ns() - start
        if rep >= 0:
            print(n, rep, *elapsed, calls, sep=',')
