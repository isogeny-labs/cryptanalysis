"""Charge the archived public chain and all affine lifting in each full preparation."""
import csv
import ctypes as C
import hashlib
from itertools import permutations
import json
from pathlib import Path
import random
import subprocess
import sys
from time import perf_counter_ns, process_time_ns

here = Path(__file__).resolve().parent
prefix = "experiments/prime-field-auxiliary-ic/snapshot/"
rev = "efb9330c1ee7e30743b7674f686cccb49f1cb25e"

def pinned(path, digest):
    data = subprocess.check_output(["git","show",f"{rev}:{prefix}{path}"],cwd=here)
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError(path)
    return data

source = pinned("prepare.py","2371663a53663a158a5e4faa87833efe888d0ae54f641d72a230e1a183ec7959")
archive = {"__name__":"archived_prepare","__file__":"prepare.py"}
exec(compile(source,"prepare.py","exec"),archive)
fixture = json.loads(pinned("algebraic/optimized/results/field31_s5_base0/public.json",
                            "a5fd508b6deacd2e2036a790946d7700929a822caf92e1fed699e6a7657fb9ca"))
p = 2**31-1
roots = fixture["structured_roots"]

def python_points(xs):
    points = []
    for x in xs:
        rhs = (x**3 + 2*x + 14) % p
        y = pow(rhs,(p+1)//4,p)
        if y*y % p == rhs:
            points.append([x,min(y,p-y)])
    return points

def native(path):
    fn = C.CDLL(str(path)).m31_lift32
    fn.argtypes = [C.POINTER(C.c_uint32)] * 2
    fn.restype = None
    words = C.c_uint32 * 32
    def points(xs):
        src, dst = words(*xs), words()
        fn(src,dst)
        return [[x,y] for x,y in zip(xs,dst) if y != p]
    return points

build = Path(sys.argv[1]).resolve()
arms = {"python":python_points, **{k:native(build/(k+".so")) for k in ("portable","neon")}}
reference = python_points(roots)
assert sorted(reference) == fixture["factor_base"]
rng = random.Random(231131)
for i in range(128):
    xs = [0,1,p-1] + [rng.randrange(p) for _ in range(29)]
    assert arms["neon"](xs) == arms["portable"](xs) == python_points(xs)
writer = csv.writer(sys.stdout,lineterminator="\n")
writer.writerow(("block","scope","arm","calls","wall_ns","cpu_ns"))
for block, order in enumerate(list(permutations(arms))*4):
    for scope in (("lift","basis") if block%2==0 else ("basis","lift")):
        calls = 64 if scope=="lift" else 12
        for name in order:
            lift = arms[name]
            wall, cpu = perf_counter_ns(), process_time_ns()
            for _ in range(calls):
                if scope=="basis":
                    aux, xs = archive["chain"](p,5,enumerate_all=True)
                else:
                    xs = roots
                result = lift(xs)
            elapsed_cpu = process_time_ns()-cpu
            elapsed_wall = perf_counter_ns()-wall
            assert result == reference
            if scope == "basis":
                assert xs == roots and aux["maps"] == fixture["auxiliary"]["maps"]
            writer.writerow((block,scope,name,calls,elapsed_wall,elapsed_cpu))
