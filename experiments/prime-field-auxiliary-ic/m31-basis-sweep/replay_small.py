"""Cold same-target M31 smaller-basis auxiliary and plain screen."""
import csv
import hashlib
import json
import os
from pathlib import Path
import random
import resource
import runpy
import shutil
import subprocess
import sys
import tempfile
from time import perf_counter_ns

HERE = Path(__file__).resolve().parent
ROOT = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=HERE, text=True).strip()
COMMON = Path(ROOT) / "experiments/prime-field-auxiliary-ic/m31-full-rust-comparison"
helpers = runpy.run_path(str(COMMON / "replay.py"))
frozen = helpers["frozen"]
Curve, chain = helpers["Curve"], helpers["chain"]


def generate(basis, size, fixture):
    p = fixture["p"]
    curve = Curve(p, a4=fixture["a"], a6=fixture["b"])
    target, generator = tuple(fixture["Q"]), tuple(fixture["P"])
    excluded = {target, generator, curve.neg(target), curve.neg(generator)}
    if basis == "auxiliary":
        _, xs = chain(p, 10 if size <= 500 else 11, enumerate_all=True)
    else:
        xs = range(10, p)
    points, seen = [], set()
    for x in xs:
        rhs = (x**3 + fixture["a"]*x + fixture["b"]) % p
        y = pow(rhs, (p + 1)//4, p)
        if y*y % p != rhs:
            continue
        point = (x, min(y, p-y))
        if x not in seen and (basis == "auxiliary" or point not in excluded):
            points.append(point)
            seen.add(x)
            if len(points) == size:
                break
    if len(points) != size:
        raise ValueError(f"basis ended early: {basis} {size} {len(points)}")
    return points


def main():
    with tempfile.TemporaryDirectory(prefix="m31-basis-sweep-", dir=os.environ.get("M31_REPLAY_TMPDIR")) as td:
        directory = Path(td)
        archive = subprocess.check_output(["git", "archive", "HEAD", "crates/prime-field-auxiliary-ic"], cwd=ROOT)
        subprocess.run(["tar", "-xf", "-", "-C", str(directory)], input=archive, check=True)
        shutil.copy2(Path(ROOT) / "crates/prime-field-auxiliary-ic/src/field.rs", directory / "crates/prime-field-auxiliary-ic/src/field.rs")
        (directory / "src").mkdir()
        (directory / "src/main.rs").write_bytes((HERE / "main.rs").read_bytes())
        (directory / "Cargo.toml").write_text('[package]\nname="m31-basis-sweep"\nversion="0.1.0"\nedition="2021"\n[dependencies]\nprime-field-auxiliary-ic={path="crates/prime-field-auxiliary-ic"}\n')
        env = os.environ.copy()
        env.update(CARGO_TARGET_DIR=str(directory / "target"), TMPDIR=str(directory),
                   M31_FAST_HASH="1", M31_TRUSTED_BATCH="1", M31_PACKED_SIGN="1",
                   M31_PAIR_BATCH="1", M31_X_BLOOM="1", M31_BLOOM_22="1",
                   M31_BLOOM_HASH_HIGH="1")
        env.pop("M31_BLOOM_HASH_LOW", None)
        subprocess.run(["cargo", "build", "--release", "--offline"], cwd=directory, env=env, check=True)
        binary = directory / "target/release/m31-basis-sweep"
        fixtures = {basis: json.loads(frozen(f"comparison/field31/{basis}/public.json"))
                    for basis in ("auxiliary", "plain")}
        generated = {}
        for basis, fixture in fixtures.items():
            generated[basis] = {size: generate(basis, size, fixture) for size in (250, 350, 500)}
            if generated[basis][500] != [tuple(p) for p in fixture["factor_base_representatives"]]:
                raise ValueError(f"500-point {basis} control differs from frozen fixture")
            for smaller in (250, 350):
                if generated[basis][smaller] != generated[basis][500][:smaller]:
                    raise ValueError(f"{basis} {smaller}-point prefix differs")
            print(f"{basis} basis sizes 250, 350 and 500 checked", file=sys.stderr)
        blocks = [(seed, repeat) for seed in range(3) for repeat in range(6)]
        random.Random(112573).shuffle(blocks)
        labels = (("auxiliary", 250), ("auxiliary", 350), ("auxiliary", 500), ("plain", 250), ("plain", 350), ("plain", 500))
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(["seed", "repeat", "position", "basis", "size", "basis_sha256", "scalar", "trials", "relations", "entries", "setup_ns", "table_ns", "elimination_ns", "rust_total_ns", "charged_wall_ns", "charged_cpu_ns"])
        for seed, repeat in blocks:
            order = labels[repeat:] + labels[:repeat]
            for position, (basis, size) in enumerate(order):
                before_child = resource.getrusage(resource.RUSAGE_CHILDREN)
                before_self = resource.getrusage(resource.RUSAGE_SELF)
                started = perf_counter_ns()
                fixture = fixtures[basis]
                points = generate(basis, size, fixture)
                if points != generated[basis][size]:
                    raise ValueError(f"regenerated basis differs: {basis} {size}")
                public = directory / "public.txt"
                public.write_text(f'{fixture["p"]} {fixture["n"]} {fixture["a"]} {fixture["b"]}\n{fixture["P"][0]} {fixture["P"][1]} {fixture["Q"][0]} {fixture["Q"][1]}\n{size}\n' + ''.join(f'{x} {y}\n' for x, y in points))
                result = json.loads(subprocess.check_output([str(binary), str(public), "flat", str(seed)], cwd=directory, text=True))
                if result["scalar"] != 123456789:
                    raise ValueError(f"unexpected public answer: {basis} {size} {seed}")
                elapsed = perf_counter_ns() - started
                child = resource.getrusage(resource.RUSAGE_CHILDREN)
                own = resource.getrusage(resource.RUSAGE_SELF)
                cpu = round(1e9 * (child.ru_utime-before_child.ru_utime + child.ru_stime-before_child.ru_stime + own.ru_utime-before_self.ru_utime + own.ru_stime-before_self.ru_stime))
                digest = hashlib.sha256(public.read_bytes()).hexdigest()
                writer.writerow([seed, repeat, position, basis, size, digest, result["scalar"], result["trials"], result["relations"], result["entries"], result["setup_ns"], result["table_ns"], result["elimination_ns"], result["total_ns"], elapsed, cpu])
                sys.stdout.flush()


if __name__ == "__main__":
    main()
