"""Cold equal-size s10/s11 auxiliary M31 basis comparison."""
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
base = runpy.run_path(str(HERE / "replay.py"))
ROOT, frozen, chain = base["ROOT"], base["frozen"], base["chain"]


def generate(depth, fixture):
    p = fixture["p"]
    _, xs = chain(p, depth, enumerate_all=True)
    points = []
    for x in xs:
        rhs = (x**3 + fixture["a"]*x + fixture["b"]) % p
        y = pow(rhs, (p + 1)//4, p)
        if y*y % p == rhs:
            points.append((x, min(y, p-y)))
            if len(points) == 500:
                break
    if len(points) != 500:
        raise ValueError(f"s{depth} returned {len(points)} lifted points")
    return points


def main():
    with tempfile.TemporaryDirectory(prefix="m31-basis-equal-", dir=os.environ.get("M31_REPLAY_TMPDIR")) as td:
        directory = Path(td)
        archive = subprocess.check_output(["git", "archive", "HEAD", "crates/prime-field-auxiliary-ic"], cwd=ROOT)
        subprocess.run(["tar", "-xf", "-", "-C", str(directory)], input=archive, check=True)
        shutil.copy2(Path(ROOT) / "crates/prime-field-auxiliary-ic/src/field.rs", directory / "crates/prime-field-auxiliary-ic/src/field.rs")
        (directory / "src").mkdir()
        (directory / "src/main.rs").write_bytes((HERE / "main.rs").read_bytes())
        (directory / "Cargo.toml").write_text('[package]\nname="m31-basis-equal"\nversion="0.1.0"\nedition="2021"\n[dependencies]\nprime-field-auxiliary-ic={path="crates/prime-field-auxiliary-ic"}\n')
        env = os.environ.copy()
        env.update(CARGO_TARGET_DIR=str(directory / "target"), TMPDIR=str(directory),
                   M31_FAST_HASH="1", M31_TRUSTED_BATCH="1", M31_PACKED_SIGN="1",
                   M31_PAIR_BATCH="1", M31_X_BLOOM="1", M31_BLOOM_22="1",
                   M31_BLOOM_HASH_HIGH="1")
        env.pop("M31_BLOOM_HASH_LOW", None)
        subprocess.run(["cargo", "build", "--release", "--offline"], cwd=directory, env=env, check=True)
        binary = directory / "target/release/m31-basis-equal"
        fixture = json.loads(frozen("comparison/field31/auxiliary/public.json"))
        expected = {depth: generate(depth, fixture) for depth in (10, 11)}
        if expected[10] != [tuple(p) for p in fixture["factor_base_representatives"]]:
            raise ValueError("s10 basis differs from frozen auxiliary fixture")
        for depth in (10, 11):
            xs = {p[0] for p in expected[depth]}
            if fixture["P"][0] in xs or fixture["Q"][0] in xs:
                raise ValueError(f"s{depth} contains public generator or target x")
        blocks = [(seed, repeat) for seed in range(3) for repeat in range(8)]
        random.Random(112577).shuffle(blocks)
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(["seed", "repeat", "position", "configuration", "basis_sha256", "scalar", "trials", "relations", "entries", "setup_ns", "table_ns", "elimination_ns", "rust_total_ns", "charged_wall_ns", "charged_cpu_ns"])
        for seed, repeat in blocks:
            order = (10, 11) if repeat % 2 else (11, 10)
            for position, depth in enumerate(order):
                before_child = resource.getrusage(resource.RUSAGE_CHILDREN)
                before_self = resource.getrusage(resource.RUSAGE_SELF)
                started = perf_counter_ns()
                points = generate(depth, fixture)
                if points != expected[depth]:
                    raise ValueError(f"s{depth} basis regeneration changed")
                public = directory / "public.txt"
                public.write_text(f'{fixture["p"]} {fixture["n"]} {fixture["a"]} {fixture["b"]}\n{fixture["P"][0]} {fixture["P"][1]} {fixture["Q"][0]} {fixture["Q"][1]}\n500\n' + ''.join(f'{x} {y}\n' for x, y in points))
                result = json.loads(subprocess.check_output([str(binary), str(public), "flat", str(seed)], cwd=directory, text=True))
                if result["scalar"] != 123456789:
                    raise ValueError(f"unexpected s{depth} answer")
                elapsed = perf_counter_ns() - started
                child = resource.getrusage(resource.RUSAGE_CHILDREN)
                own = resource.getrusage(resource.RUSAGE_SELF)
                cpu = round(1e9 * (child.ru_utime-before_child.ru_utime + child.ru_stime-before_child.ru_stime + own.ru_utime-before_self.ru_utime + own.ru_stime-before_self.ru_stime))
                digest = hashlib.sha256(public.read_bytes()).hexdigest()
                writer.writerow([seed, repeat, position, f"s{depth}", digest, result["scalar"], result["trials"], result["relations"], result["entries"], result["setup_ns"], result["table_ns"], result["elimination_ns"], result["total_ns"], elapsed, cpu])
                sys.stdout.flush()


if __name__ == "__main__":
    main()
