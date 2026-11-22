"""Run the public ABI through ctypes. Pass the compiled library path."""
import ctypes as C
from pathlib import Path
import random
import sys

P = 2**31 - 1
U = C.c_uint32
inverse = C.CDLL(str(Path(sys.argv[1]).resolve())).m31_batch_inverse
inverse.argtypes = [C.POINTER(U), C.POINTER(U), C.c_size_t]
inverse.restype = None
inverse(None, None, 0)
rng = random.Random(291153)
edges = [0, 1, P-1, P, P+1, 2*P-1, 2*P, 2*P+1]
checks = 0
for n in [*range(257), 511, 512, 513, 4095, 4096, 4097]:
    xs = [rng.choice(edges) if i % 3 == 0 else rng.getrandbits(32) for i in range(n)]
    expected = [pow(x, P-2, P) for x in xs]
    for inplace in [False, True]:
        sentinel = 0xdeadbeef
        src = (U*(n+2))(sentinel, *xs, sentinel)
        dst = src if inplace else (U*(n+2))(sentinel, *([sentinel]*n), sentinel)
        inverse(C.cast(C.byref(src, 4), C.POINTER(U)),
                C.cast(C.byref(dst, 4), C.POINTER(U)), n)
        assert dst[:] == [sentinel, *expected, sentinel]
        if not inplace:
            assert src[:] == [sentinel, *xs, sentinel]
        checks += n
print("verified outputs", checks)
