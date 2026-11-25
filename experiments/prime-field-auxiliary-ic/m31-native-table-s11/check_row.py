"""Independent public affine check of selected full native table rows."""
import ctypes as C
import json
from pathlib import Path
import runpy
import sys

U = C.c_uint32
helpers = runpy.run_path(str(Path(__file__).resolve().parent.parent / "m31-basis-sweep/replay.py"))
scan = C.CDLL(str(Path(sys.argv[1]).resolve())).m31_sum_row
scan.argtypes = [U, U, C.POINTER(U), C.POINTER(U), C.POINTER(U), C.POINTER(U),
                C.POINTER(U), C.POINTER(U), C.c_size_t]
scan.restype = C.c_int
for basis in ("auxiliary", "plain"):
    fixture = json.loads(helpers["frozen"](f"comparison/field31/{basis}/public.json"))
    curve = helpers["Curve"](fixture["p"], a4=fixture["a"], a6=fixture["b"])
    for size in (500, 1013):
        points = helpers["generate"](basis, size, fixture)
        signed = [q for p in points for q in (p, curve.neg(p))]
        x = (U * len(signed))(*(p[0] for p in signed))
        y = (U * len(signed))(*(p[1] for p in signed))
        checked = exceptional = 0
        for i in (0, len(signed)//2 // 2 * 2, len(signed)-2):
            count = len(signed)-i
            out_x = (U * (count+2))(*([0xDEADBEEF]*(count+2)))
            out_y = (U * (count+2))(*([0xDEADBEEF]*(count+2)))
            den, inverse = (U * count)(), (U * count)()
            xptr = C.cast(C.byref(out_x, 4), C.POINTER(U))
            yptr = C.cast(C.byref(out_y, 4), C.POINTER(U))
            assert scan(signed[i][0], signed[i][1], C.cast(C.byref(x, 4*i), C.POINTER(U)),
                        C.cast(C.byref(y, 4*i), C.POINTER(U)), xptr, yptr, den,
                        inverse, count) == 0
            assert out_x[0] == out_x[-1] == out_y[0] == out_y[-1] == 0xDEADBEEF
            for off in range(count):
                expected = curve.add(signed[i], signed[i+off])
                if signed[i][0] == signed[i+off][0]:
                    assert out_x[off+1] == 0xFFFFFFFF
                    exceptional += 1
                else:
                    assert expected == (out_x[off+1], out_y[off+1]), (basis, size, i, off)
                checked += 1
        print(f"{basis} {size}: {checked} exact/exceptional outputs, {exceptional} fallbacks")
