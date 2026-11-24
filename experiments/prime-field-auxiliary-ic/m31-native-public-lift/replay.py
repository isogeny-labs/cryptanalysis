"""Run python3 replay.py from a checkout with the frozen M31 Git objects."""
import ctypes
import json
from pathlib import Path
import random
import subprocess
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
SNAPSHOT = "f9c7b49e7:experiments/prime-field-auxiliary-ic/snapshot/"
P = 2**31 - 1


def archived(path):
    return json.loads(subprocess.check_output(["git", "show", SNAPSHOT + path], cwd=HERE))


def auxiliary_inputs():
    chain = archived("auxiliary_31.json")
    x, y = chain["auxiliary_generator"]
    u, v = chain["kernel_generator"]
    coordinates = []
    for _ in range(chain["kernel_order"]):
        coordinates.append(x)
        slope = (v - y) * pow(u - x, -1, P) % P
        z = (slope*slope - x - u) % P
        x, y = z, (slope*(x - z) - y) % P
    assert [x, y] == chain["auxiliary_generator"]
    assert len(set(coordinates)) == 1024
    return coordinates


def replay(kernel):
    word = ctypes.c_uint32
    pointer = ctypes.POINTER(word)
    kernel.argtypes = [pointer, ctypes.c_size_t, word, word, pointer]
    kernel.restype = None

    def lift(xs, a, b):
        buffer = word * len(xs)
        out = buffer()
        kernel(buffer(*xs), len(xs), a, b, out)
        return list(out)

    boundary = [0, 1, 2, P // 2, P-2, P-1]
    xs = boundary + random.Random(310030).sample(range(P), 16384)
    for a, b in [(2, 14), (0, 0), (P-1, P-1)]:
        for x, actual in zip(xs, lift(xs, a, b), strict=True):
            rhs = (x**3 + a*x + b) % P
            y = pow(rhs, (P+1)//4, P)
            assert actual == (min(y, P-y) if y*y % P == rhs else P)
    assert lift([], 2, 14) == []

    for arm, inputs in [('auxiliary', auxiliary_inputs()), ('plain', range(10, 1055))]:
        public = archived(f"comparison/field31/{arm}/public.json")
        excluded = {tuple(public[k]) for k in ('P', 'Q')} if arm == 'plain' else set()
        excluded |= {(x, -y % P) for x, y in excluded}
        points = [[x, y] for x, y in zip(inputs, lift(inputs, public['a'], public['b']), strict=True)
                  if y != P and (x, y) not in excluded]
        assert len(points) == 500 and points == public['factor_base_representatives']
    print("49170 differential cases and both ordered 500-point bases passed")


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("Replay requires assertions")
    with TemporaryDirectory() as tmp:
        library = Path(tmp) / "lift.so"
        flag = "-dynamiclib" if sys.platform == "darwin" else "-shared"
        subprocess.run(["cc", "-O3", "-std=c11", "-Wall", "-Wextra", "-Werror", "-fPIC",
                        flag, str(HERE / "lift.c"), "-o", str(library)], check=True)
        replay(ctypes.CDLL(str(library)).lift_ordinates)
