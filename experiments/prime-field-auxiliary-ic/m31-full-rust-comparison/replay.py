"""Paired, setup-charged replay on the frozen public M31 fixture."""
import csv
import hashlib
import json
import random
import resource
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from time import perf_counter_ns

HERE = Path(__file__).resolve().parent
ROOT = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=HERE, text=True).strip()
PREFIX = "experiments/prime-field-auxiliary-ic/snapshot/"

def frozen(path):
    return subprocess.check_output(["git", "show", "HEAD:" + PREFIX + path], cwd=ROOT)

source = frozen("prepare.py")
namespace = {"__name__": "frozen_prepare", "__file__": "frozen_prepare.py"}
exec(compile(source, "frozen_prepare.py", "exec"), namespace)
Curve, chain = namespace["Curve"], namespace["chain"]

def generate(basis, fixture):
    p = fixture["p"]
    curve = Curve(p, a4=fixture["a"], a6=fixture["b"])
    target = tuple(fixture["Q"])
    generator = tuple(fixture["P"])
    excluded = {target, generator, curve.neg(target), curve.neg(generator)}
    def lift(x):
        rhs = (x**3 + fixture["a"]*x + fixture["b"]) % p
        y = pow(rhs, (p+1)//4, p)
        if y*y % p != rhs:
            return None
        return x, min(y, p-y)
    points = []
    seen = set()
    if basis == "auxiliary":
        _, xs = chain(p, 10, enumerate_all=True)
        candidates = iter(xs)
    else:
        candidates = iter(range(10, p))
    for x in candidates:
        point = lift(x)
        if point is not None and point[0] not in seen and (basis == "auxiliary" or point not in excluded):
            points.append(point)
            seen.add(point[0])
            if len(points) == 500:
                break
    if len(points) != 500:
        raise ValueError("factor base generation stopped early")
    return points

def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        archive = subprocess.check_output(["git", "archive", "HEAD", "crates/prime-field-auxiliary-ic"], cwd=ROOT)
        subprocess.run(["tar", "-xf", "-", "-C", str(tmp)], input=archive, check=True)
        (tmp / "src").mkdir()
        (tmp / "src/main.rs").write_bytes((HERE / "main.rs").read_bytes())
        (tmp / "Cargo.toml").write_text('[package]\nname="m31-full-comparison"\nversion="0.1.0"\nedition="2021"\n[dependencies]\nprime-field-auxiliary-ic={path="crates/prime-field-auxiliary-ic"}\n')
        subprocess.run(["cargo", "build", "--release", "--offline"], cwd=tmp, check=True)
        fixtures = {}
        for basis in ("auxiliary", "plain"):
            path = f"comparison/field31/{basis}/public.json"
            fixtures[basis] = json.loads(frozen(path))
        blocks = [(basis, seed, round_number) for basis in fixtures for seed in range(3) for round_number in range(8)]
        random.Random(112527).shuffle(blocks)
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(["basis", "seed", "round", "position", "mode", "basis_sha256", "scalar", "trials", "relations", "entries", "setup_ns", "table_ns", "elimination_ns", "rust_total_ns", "charged_wall_ns", "charged_cpu_ns"])
        for basis, seed, round_number in blocks:
            fixture = fixtures[basis]
            order = ("flat", "reflected") if round_number % 2 else ("reflected", "flat")
            for position, mode in enumerate(order):
                before = resource.getrusage(resource.RUSAGE_CHILDREN)
                parent_cpu = resource.getrusage(resource.RUSAGE_SELF)
                started = perf_counter_ns()
                points = generate(basis, fixture)
                if points != [tuple(p) for p in fixture["factor_base_representatives"]]:
                    raise ValueError("regenerated basis differs from frozen fixture")
                public = tmp / "public.txt"
                public.write_text(f'{fixture["p"]} {fixture["n"]} {fixture["a"]} {fixture["b"]}\n{fixture["P"][0]} {fixture["P"][1]} {fixture["Q"][0]} {fixture["Q"][1]}\n500\n' + ''.join(f'{x} {y}\n' for x,y in points))
                output = subprocess.check_output([str(tmp / "target/release/m31-full-comparison"), str(public), mode, str(seed)], cwd=tmp, text=True)
                result = json.loads(output)
                if result["scalar"] != 123456789:
                    raise ValueError("unexpected recovered scalar")
                elapsed = perf_counter_ns() - started
                child = resource.getrusage(resource.RUSAGE_CHILDREN)
                own = resource.getrusage(resource.RUSAGE_SELF)
                cpu_ns = round(1e9 * (child.ru_utime-before.ru_utime + child.ru_stime-before.ru_stime + own.ru_utime-parent_cpu.ru_utime + own.ru_stime-parent_cpu.ru_stime))
                digest = hashlib.sha256(public.read_bytes()).hexdigest()
                writer.writerow([basis, seed, round_number, position, mode, digest, result["scalar"], result["trials"], result["relations"], result["entries"], result["setup_ns"], result["table_ns"], result["elimination_ns"], result["total_ns"], elapsed, cpu_ns])
                sys.stdout.flush()

if __name__ == "__main__":
    main()
