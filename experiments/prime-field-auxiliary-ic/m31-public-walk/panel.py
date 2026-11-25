"""Replay full preparation for four public auxiliary-walk controls."""
import csv
import ctypes as c
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("chain_panel", HERE.parent/"m31-projective-check"/"replay.py")
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)


def main():
    if not __debug__:
        raise RuntimeError("archive validation requires Python assertions")
    src = prior.read("prepare.py")
    pub = json.loads(prior.read("public.json"))
    assert pub["p"] == 2**31-1 and pub.get("cofactor", 1) == 1
    expected = list(map(tuple, pub["factor_base_representatives"]))
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root/"common.hpp").write_text(prior.read("comparison/common.hpp"))
        lib = root/"public.so"
        subprocess.run(["c++", "-O3", "-mcpu=native", "-std=c++17", "-shared", "-fPIC",
                        "-DFIELD_BITS=31", "-I", root, HERE/"walk.cpp",
                        HERE.parent/"m31-root-schedule"/"root.cpp",
                        HERE.parent/"m31-projective-check"/"verify.cpp", "-o", lib], check=True)
        dll = c.CDLL(str(lib))
        wp = c.POINTER(prior.W)
        roots = dll.m31_checked_roots
        roots.argtypes = [wp,wp,c.c_size_t]
        roots.restype = None
        verify = dll.check_chain
        verify.argtypes = [wp,c.c_size_t,c.POINTER(prior.Step),c.c_size_t,prior.W,c.c_bool,
                           c.POINTER(c.c_uint8)]
        verify.restype = None
        walk = dll.public_walk
        walk.argtypes = [c.c_uint64]*4 + [c.c_bool, wp, wp]
        walk.restype = c.c_bool

        def native_walk(t, g, n, levels):
            assert n == 1024
            xs = (prior.W*n)()
            successor = (prior.W*2)()
            assert walk(*t, *g, levels, xs, successor)
            return list(xs), tuple(successor)

        start = src.index("    for i in range(checked_count):")
        end = src.index("    assert len(set(V))", start)
        serial_loop = src[start:end]
        assert serial_loop.count(" and eval_chain(R[0]) == 0") == 1
        chains = []
        for arm in range(4):
            if arm == 0:
                patched = src
            else:
                loop = serial_loop.replace(" and eval_chain(R[0]) == 0", "") if arm == 1 else (
                    "    V, R = native_walk(T, G, checked_count, levels)\n")
                patched = src[:start] + loop + "    assert validate(V,maps,c)\n" + src[end:]
            mod = types.ModuleType("public_setup")
            mod.__file__ = str(HERE/"archived_prepare.py")
            mod.native_walk, mod.levels = native_walk, arm == 3
            mod.validate = lambda xs, ms, t: all(prior.native(verify, True, xs, ms, t))
            exec(compile(patched, mod.__file__, "exec"), mod.__dict__)
            chains.append(mod.chain)
        curve = mod.Curve(prior.P, a4=pub["a"], a6=pub["b"])
        excluded = prior.excluded_points(pub, curve)
        control, _ = prior.build_controls(pub, curve, chains[0])
        identity = chains[0](prior.P, 10, enumerate_all=True)
        for chain in chains[1:]:
            assert chain(prior.P, 10, enumerate_all=True) == identity
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(["block","position","arm","seconds"])
        for block in range(24):
            for position, shift in enumerate((0,1,3,2)):
                arm = (block+shift) % 4
                if arm == 0:
                    points, seconds = control["auxiliary"]()
                else:
                    points, seconds = prior.ffi_phase("auxiliary",pub,chains[arm],excluded,roots)
                assert points == expected
                writer.writerow([block,position,arm,seconds])


if __name__ == "__main__":
    main()
