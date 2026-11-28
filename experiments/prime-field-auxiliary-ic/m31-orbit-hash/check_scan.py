"""Independent affine group-law check of the native M31 candidate scan."""
import ctypes as C
import json
from pathlib import Path
import runpy
import sys

U = C.c_uint32
helpers = runpy.run_path(str(Path(__file__).resolve().parent.parent / "m31-full-rust-comparison/replay.py"))
lib = C.CDLL(str(Path(sys.argv[1]).resolve()))
scan = lib.m31_scan_pairs
scan.argtypes = [U, U, C.POINTER(U), C.POINTER(U), C.POINTER(C.c_uint64),
                 C.POINTER(U), C.POINTER(U), C.c_size_t]
scan.restype = C.c_size_t
all_ones = (C.c_uint64 * (1 << 16))(*([2**64 - 1] * (1 << 16)))

for basis in ("auxiliary", "plain"):
    fixture = json.loads(helpers["frozen"](f"comparison/field31/{basis}/public.json"))
    curve = helpers["Curve"](fixture["p"], a4=fixture["a"], a6=fixture["b"])
    signed = [q for p in helpers["generate"](basis, fixture) for q in (p, curve.neg(p))]
    minus = [curve.neg(p) for p in signed]
    left = tuple(fixture["Q"])
    assert all(p[0] != left[0] for p in minus)
    bx = (U * 1000)(*(p[0] for p in minus))
    by = (U * 1000)(*(p[1] for p in minus))
    indices = (U * 1002)(*([0xDEADBEEF] * 1002))
    keys = (U * 1002)(*([0xDEADBEEF] * 1002))
    index_out = C.cast(C.byref(indices, 4), C.POINTER(U))
    key_out = C.cast(C.byref(keys, 4), C.POINTER(U))
    count = scan(left[0], left[1], bx, by, all_ones, index_out, key_out, 500)
    assert count == 1000
    assert indices[0] == indices[1001] == keys[0] == keys[1001] == 0xDEADBEEF
    for k, point in enumerate(minus):
        q = curve.add(left, point)
        assert q is not None
        assert indices[k + 1] == k
        assert keys[k + 1] == (q[0] << 1) | (q[1] & 1), (basis, k)
    original = bx[0], bx[1]
    bx[0] = bx[1] = left[0]
    assert scan(left[0], left[1], bx, by, all_ones, index_out, key_out, 500) == C.c_size_t(-1).value
    bx[0], bx[1] = original
    print(f"{basis}: 1,000 exact point keys, order, and exceptional fallback verified")
