"""Replay only the public setup phases on the pinned M31 fixtures."""
import ast
import csv
import ctypes
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import types

HERE = Path(__file__).resolve().parent
REV = "efb9330c1ee7e30743b7674f686cccb49f1cb25e"
SNAPSHOT = "experiments/prime-field-auxiliary-ic/snapshot"
WIDTH = 64


def read(path):
    return subprocess.check_output(["git", "show", f"{REV}:{SNAPSHOT}/{path}"], cwd=HERE, text=True)


def build_controls(public, curve, chain):
    # Extract the timed statements, preserving the original clock boundaries.
    tree = ast.parse(read("comparison/prepare_comparison.py"))
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    loop = next(n for n in main.body if isinstance(n, ast.For))
    lift = next(n for n in loop.body if isinstance(n, ast.FunctionDef) and n.name == "lift")
    env = dict(E=curve, h=1, p=public["p"], public=public, chain=chain, s=10,
               K=500, time=time, excluded=excluded_points(public, curve))
    exec(compile(ast.Module([lift], []), "<archived lift>", "exec"), env)
    phases = {}
    for label, output in [("auxiliary", "points"), ("plain", "plain")]:
        stop = next(i for i, n in enumerate(loop.body) if isinstance(n, ast.Assign)
                    and ast.unparse(n.targets[0]) == label + "_seconds")
        start = max(i for i, n in enumerate(loop.body[:stop]) if isinstance(n, ast.Assign)
                    and ast.unparse(n.targets[0]) == "start")
        body = ast.unparse(ast.Module(loop.body[start:stop+1], []))
        source = "def phase():\n" + "\n".join("    " + line for line in body.splitlines())
        exec(source + f"\n    return {output}, {label}_seconds", env)
        phases[label] = env["phase"]
    return phases, env


def excluded_points(public, curve):
    points = [tuple(public[k]) for k in ("P", "Q")]
    return set(points + [curve.neg(point) for point in points])


def ffi_phase(method, public, chain, excluded, roots):
    p, a, b = (public[k] for k in ("p", "a", "b"))
    start = time.perf_counter()
    points, seen = [], set()
    auxiliary = method == "auxiliary"
    source = chain(p, 10, enumerate_all=True)[1] if auxiliary else None
    offset = 0
    while (offset < len(source)) if auxiliary else (len(points) < 500):
        xs = source[offset:offset+WIDTH] if auxiliary else range(10+offset, 10+offset+WIDTH)
        buf = (ctypes.c_uint32 * len(xs))(*((x**3 + a*x + b) % p for x in xs))
        roots(buf, buf, len(xs))
        for x, y in zip(xs, buf):
            if y == p or x in seen or (not auxiliary and (x, y) in excluded):
                continue
            seen.add(x)
            points.append((x, y))
            if not auxiliary and len(points) == 500:
                break
        offset += WIDTH
    return points, time.perf_counter()-start


def main():
    prepare = types.ModuleType("archived_prepare")
    prepare.__file__ = str(HERE / "archived_prepare.py")
    exec(compile(read("prepare.py"), prepare.__file__, "exec"), prepare.__dict__)
    original = json.loads(read("public.json"))
    assert original.get("cofactor", 1) == 1 and original["p"] == 2**31-1
    public = {k: original[k] for k in ("p", "n", "a", "b", "P", "Q")}
    curve = prepare.Curve(public["p"], a4=public["a"], a6=public["b"])
    excluded = excluded_points(public, curve)
    control, env = build_controls(public, curve, prepare.chain)
    baseline = env["lift"]
    expected = {label: list(map(tuple, json.loads(read(
        f"comparison/field31/{label}/public.json"))["factor_base_representatives"]))
                for label in control}

    def cofactor_one(x):
        p = public["p"]
        rhs = (x**3 + public["a"]*x + public["b"]) % p
        y = pow(rhs, (p+1)//4, p)
        return (x, min(y, p-y)) if y*y % p == rhs else None

    with tempfile.TemporaryDirectory() as tmp:
        libraries = []
        for mode in ("portable", "native"):
            path = Path(tmp) / (mode + ".so")
            flags = ["-DM31_ROOT_PORTABLE"] if mode == "portable" else []
            subprocess.run(["c++", "-std=c++17", "-O3", "-mcpu=native", "-shared", "-fPIC",
                            *flags, HERE.parent/"m31-root-schedule"/"root.cpp", "-o", path], check=True)
            fn = ctypes.CDLL(str(path)).m31_checked_roots
            fn.argtypes = (ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32), ctypes.c_size_t)
            fn.restype = None
            libraries.append(fn)
        out = csv.writer(sys.stdout, lineterminator="\n")
        out.writerow(["block", "position", "basis", "arm", "seconds"])
        for block in range(24):
            for basis in (("auxiliary", "plain") if block%2 == 0 else ("plain", "auxiliary")):
                for pos, shift in enumerate((0,1,3,2)):
                    arm = (shift + block) % 4
                    if arm < 2:
                        env["lift"] = (baseline, cofactor_one)[arm]
                        points, elapsed = control[basis]()
                    else:
                        points, elapsed = ffi_phase(basis, public, prepare.chain, excluded, libraries[arm-2])
                    assert points == expected[basis]
                    out.writerow([block, pos, basis, arm, elapsed])


if __name__ == "__main__":
    main()
