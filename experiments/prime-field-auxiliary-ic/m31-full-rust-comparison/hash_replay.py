"""Matched full-collector comparison of two flat-index hash functions."""
import csv
import hashlib
import json
import os
from pathlib import Path
import random
import resource
import runpy
import subprocess
import sys
import tempfile
from time import perf_counter_ns

HERE = Path(__file__).resolve().parent
helpers = runpy.run_path(str(HERE / "replay.py"))
ROOT = helpers["ROOT"]
frozen = helpers["frozen"]
generate = helpers["generate"]


def main():
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        archive = subprocess.check_output(["git", "archive", "HEAD", "crates/prime-field-auxiliary-ic"], cwd=ROOT)
        subprocess.run(["tar", "-xf", "-", "-C", str(directory)], input=archive, check=True)
        (directory / "src").mkdir()
        (directory / "src/main.rs").write_bytes((HERE / "main.rs").read_bytes())
        (directory / "Cargo.toml").write_text('[package]\nname="m31-full-comparison"\nversion="0.1.0"\nedition="2021"\n[dependencies]\nprime-field-auxiliary-ic={path="crates/prime-field-auxiliary-ic"}\n')
        binaries = {}
        for label, fast in (("splitmix", False), ("multiply", True)):
            build_dir = directory / f"target-{label}"
            env = os.environ.copy()
            env["CARGO_TARGET_DIR"] = str(build_dir)
            if fast:
                env["M31_FAST_HASH"] = "1"
            else:
                env.pop("M31_FAST_HASH", None)
            subprocess.run(["cargo", "build", "--release", "--offline"], cwd=directory, env=env, check=True)
            binaries[label] = build_dir / "release/m31-full-comparison"
        fixtures = {basis: json.loads(frozen(f"comparison/field31/{basis}/public.json"))
                    for basis in ("auxiliary", "plain")}
        blocks = [(basis, seed, repeat) for basis in fixtures for seed in range(3) for repeat in range(8)]
        random.Random(112528).shuffle(blocks)
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(["basis", "seed", "repeat", "position", "hash", "basis_sha256", "scalar", "trials", "relations", "entries", "table_ns", "rust_total_ns", "charged_wall_ns", "charged_cpu_ns"])
        for basis, seed, repeat in blocks:
            fixture = fixtures[basis]
            order = ("splitmix", "multiply") if repeat % 2 else ("multiply", "splitmix")
            for position, label in enumerate(order):
                before_child = resource.getrusage(resource.RUSAGE_CHILDREN)
                before_self = resource.getrusage(resource.RUSAGE_SELF)
                started = perf_counter_ns()
                points = generate(basis, fixture)
                if points != [tuple(p) for p in fixture["factor_base_representatives"]]:
                    raise ValueError("regenerated basis differs from frozen fixture")
                public = directory / "public.txt"
                public.write_text(f'{fixture["p"]} {fixture["n"]} {fixture["a"]} {fixture["b"]}\n{fixture["P"][0]} {fixture["P"][1]} {fixture["Q"][0]} {fixture["Q"][1]}\n500\n' + ''.join(f'{x} {y}\n' for x, y in points))
                output = subprocess.check_output([str(binaries[label]), str(public), "flat", str(seed)], cwd=directory, text=True)
                result = json.loads(output)
                if result["scalar"] != 123456789:
                    raise ValueError("unexpected public answer")
                elapsed = perf_counter_ns() - started
                child = resource.getrusage(resource.RUSAGE_CHILDREN)
                own = resource.getrusage(resource.RUSAGE_SELF)
                cpu = round(1e9 * (child.ru_utime - before_child.ru_utime + child.ru_stime - before_child.ru_stime + own.ru_utime - before_self.ru_utime + own.ru_stime - before_self.ru_stime))
                writer.writerow([basis, seed, repeat, position, label, hashlib.sha256(public.read_bytes()).hexdigest(), result["scalar"], result["trials"], result["relations"], result["entries"], result["table_ns"], result["total_ns"], elapsed, cpu])
                sys.stdout.flush()


if __name__ == "__main__":
    main()
