"""Paired cold M31 bitmap collector and archived C++ rho distance."""
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
helpers = runpy.run_path(str(HERE / "replay.py"))
ROOT = helpers["ROOT"]
frozen = helpers["frozen"]
generate = helpers["generate"]


def cpu_usage():
    child = resource.getrusage(resource.RUSAGE_CHILDREN)
    parent = resource.getrusage(resource.RUSAGE_SELF)
    return child.ru_utime + child.ru_stime + parent.ru_utime + parent.ru_stime


def main():
    with tempfile.TemporaryDirectory(prefix="m31-rho-distance-", dir=os.environ.get("M31_REPLAY_TMPDIR")) as td:
        directory = Path(td)
        archive = subprocess.check_output(["git", "archive", "HEAD", "crates/prime-field-auxiliary-ic"], cwd=ROOT)
        subprocess.run(["tar", "-xf", "-", "-C", str(directory)], input=archive, check=True)
        shutil.copy2(Path(ROOT) / "crates/prime-field-auxiliary-ic/src/field.rs", directory / "crates/prime-field-auxiliary-ic/src/field.rs")
        (directory / "src").mkdir()
        (directory / "src/main.rs").write_bytes((HERE / "main.rs").read_bytes())
        (directory / "Cargo.toml").write_text('[package]\nname="m31-full-comparison"\nversion="0.1.0"\nedition="2021"\n[dependencies]\nprime-field-auxiliary-ic={path="crates/prime-field-auxiliary-ic"}\n')
        env = os.environ.copy()
        env.update(CARGO_TARGET_DIR=str(directory / "target-bitmap"), TMPDIR=str(directory),
                   M31_FAST_HASH="1", M31_TRUSTED_BATCH="1", M31_PACKED_SIGN="1",
                   M31_PAIR_BATCH="1", M31_X_BLOOM="1")
        env.pop("M31_X_FILTER", None)
        subprocess.run(["cargo", "build", "--release", "--offline"], cwd=directory, env=env, check=True)
        bitmap = directory / "target-bitmap/release/m31-full-comparison"
        common = directory / "common.hpp"
        rho_cpp = directory / "compare_rho.cpp"
        common.write_bytes(frozen("comparison/common.hpp"))
        rho_cpp.write_bytes(frozen("comparison/compare_rho.cpp"))
        rho = directory / "compare_rho"
        subprocess.run(["c++", "-std=c++17", "-O3", "-DFIELD_BITS=31", str(rho_cpp), "-o", str(rho)], check=True)
        fixtures = {basis: json.loads(frozen(f"comparison/field31/{basis}/public.json"))
                    for basis in ("auxiliary", "plain")}
        frozen_rho = frozen("comparison/field31/rho/public.txt")
        for basis, fixture in fixtures.items():
            points = generate(basis, fixture)
            if points != [tuple(p) for p in fixture["factor_base_representatives"]]:
                raise ValueError("regenerated audit basis differs from fixture")
            reference = json.loads(frozen("comparison/field31/rho/public.json"))
            for key in ("p", "n", "a", "b", "P", "Q"):
                if fixture[key] != reference[key]:
                    raise ValueError(f"rho identity differs for {basis}: {key}")
        blocks = [(basis, seed, repeat) for basis in fixtures for seed in range(3) for repeat in range(8)]
        random.Random(112547).shuffle(blocks)
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(["basis", "seed", "repeat", "position", "configuration", "scalar", "charged_wall_ns", "charged_cpu_ns", "basis_sha256", "trials_or_steps", "relations", "entries"])
        for basis, seed, repeat in blocks:
            fixture = fixtures[basis]
            order = ("bitmap", "rho") if repeat % 2 else ("rho", "bitmap")
            for position, label in enumerate(order):
                started_cpu = cpu_usage()
                started = perf_counter_ns()
                if label == "bitmap":
                    points = generate(basis, fixture)
                    if points != [tuple(p) for p in fixture["factor_base_representatives"]]:
                        raise ValueError("regenerated timed basis differs from fixture")
                    public = directory / "bitmap-public.txt"
                    public.write_text(f'{fixture["p"]} {fixture["n"]} {fixture["a"]} {fixture["b"]}\n{fixture["P"][0]} {fixture["P"][1]} {fixture["Q"][0]} {fixture["Q"][1]}\n500\n' + ''.join(f'{x} {y}\n' for x, y in points))
                    result = json.loads(subprocess.check_output([str(bitmap), str(public), "flat", str(seed)], cwd=directory, text=True))
                    scalar = result["scalar"]
                    digest = hashlib.sha256(public.read_bytes()).hexdigest()
                    trials, relations, entries = result["trials"], result["relations"], result["entries"]
                else:
                    rho_dir = directory / "rho-run"
                    rho_dir.mkdir(exist_ok=True)
                    (rho_dir / "public.txt").write_bytes(frozen_rho)
                    subprocess.check_output([str(rho), str(seed)], cwd=rho_dir, text=True)
                    result = json.loads((rho_dir / "metrics.json").read_text())
                    scalar = result["recovered"]
                    digest = hashlib.sha256(frozen_rho).hexdigest()
                    trials, relations, entries = result["walk_steps"], "", ""
                if scalar != 123456789:
                    raise ValueError(f"unexpected {label} scalar on {basis} seed {seed}")
                elapsed = perf_counter_ns() - started
                cpu = round((cpu_usage() - started_cpu) * 1e9)
                writer.writerow([basis, seed, repeat, position, label, scalar, elapsed, cpu, digest, trials, relations, entries])
                sys.stdout.flush()


if __name__ == "__main__":
    main()
