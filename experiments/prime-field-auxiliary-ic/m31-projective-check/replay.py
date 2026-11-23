"""Time complete public M31 auxiliary preparation, including all coordinate checks."""
import argparse
import csv
import ctypes as c
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import types

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "m31-public-basis-replay"))
from panel import build_controls, excluded_points, ffi_phase, read

P = 2**31-1
W = c.c_uint32


class Step(c.Structure):
    _fields_ = [(name, W) for name in ("r", "a", "b")]


def reference(x, steps):
    for step in steps:
        u = (x-step["r"]) % P
        if not u:
            return None
        x = (u + step["A"] + step["B"] * pow(u, -1, P)) % P
    return x


def native(verify, projective, xs, maps, target):
    packed = (Step * len(maps))(*(Step(s["r"], s["A"], s["B"]) for s in maps))
    flags = (c.c_uint8 * len(xs))()
    verify((W*len(xs))(*xs), len(xs), packed, len(maps), target, projective, flags)
    return list(flags)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-control", action="store_true")
    args = parser.parse_args()
    src = read("prepare.py")
    original = json.loads(read("public.json"))
    expected = list(map(tuple, original["factor_base_representatives"]))
    assert original.get("cofactor", 1) == 1 and original["p"] == P
    with tempfile.TemporaryDirectory() as tmp:
        lib = Path(tmp)/"public.so"
        subprocess.run(["c++", "-std=c++17", "-O3", "-mcpu=native", "-shared", "-fPIC",
                        HERE/"verify.cpp", HERE.parent/"m31-root-schedule"/"root.cpp",
                        "-o", lib], check=True)
        dll = c.CDLL(str(lib))
        roots = dll.m31_checked_roots
        roots.argtypes = [c.POINTER(W), c.POINTER(W), c.c_size_t]
        roots.restype = None
        verify = dll.check_chain
        verify.argtypes = [c.POINTER(W), c.c_size_t, c.POINTER(Step), c.c_size_t,
                           W, c.c_bool, c.POINTER(c.c_uint8)]
        verify.restype = None

        # Keep the point walk, chain construction, and all surrounding assertions.
        # Move only the per-coordinate condition for the three batched arms.
        check = "assert R is not None and eval_chain(R[0]) == 0"
        end = "    assert len(set(V)) == len(V)"
        assert src.count(check) == src.count(end) == 1
        deferred = src.replace(check, "assert R is not None").replace(
            end, "    assert validate(V, maps, c)\n" + end)
        validators = [None, lambda xs, ms, t: all(reference(x, ms) == t for x in xs),
                      lambda xs, ms, t: all(native(verify, False, xs, ms, t)),
                      lambda xs, ms, t: all(native(verify, True, xs, ms, t))]
        chains = []
        for validator in validators:
            module = types.ModuleType("archived_public_setup")
            module.__file__ = str(HERE/"archived_prepare.py")
            module.validate = validator
            exec(compile(deferred if validator else src, module.__file__, "exec"), module.__dict__)
            chains.append(module.chain)
        curve = module.Curve(P, a4=original["a"], a6=original["b"])
        excluded = excluded_points(original, curve)
        maps = chains[0](P, 10, enumerate_all=True)[0]["maps"]
        rng = random.Random(20261122)
        xs = [0, 1, P-1, *(s["r"] for s in maps), *(rng.randrange(P) for _ in range(200))]
        for ms in [[], *[[s] for s in maps], maps, [{"r": 0, "A": 0, "B": 0}]*3]:
            vals = [reference(x, ms) for x in xs]
            for target in (0, 1, P-1, next(v for v in vals if v is not None)):
                ref = [v == target for v in vals]
                for use_projective in (False, True):
                    assert native(verify, use_projective, xs, ms, target) == ref

        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(["block","position","arm","seconds"])
        if args.full_control:
            phases, _ = build_controls(original, curve, chains[0])
            for block in range(24):
                for position in range(2):
                    arm = (block + position) % 2
                    if arm == 0:
                        points, seconds = phases["auxiliary"]()
                    else:
                        points, seconds = ffi_phase("auxiliary", original, chains[3], excluded, roots)
                    assert points == expected
                    writer.writerow([block, position, arm, seconds])
            return
        for block in range(24):
            for position, shift in enumerate((0,1,3,2)):
                arm = (block+shift) % 4
                points, seconds = ffi_phase("auxiliary", original, chains[arm], excluded, roots)
                assert points == expected
                writer.writerow([block,position,arm,seconds])


if __name__ == "__main__":
    main()
