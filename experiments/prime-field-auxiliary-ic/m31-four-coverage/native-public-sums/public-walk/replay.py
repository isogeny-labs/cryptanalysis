"""Run python3 replay.py > timings.csv on a native little-endian host.

The timed fresh process initializes all public points, generates the prefix
and writes its coordinates to /dev/null. Full-stream checks run separately.
"""
import csv
import hashlib
import itertools
from pathlib import Path
import random
import resource
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
NATIVE = "14c8370:experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/native_v2.cpp"
CASES = (
    (14706000, "668c0a2f5cd8f8bcbc0c2268da317408875f8520e3c83c0015fec3c50cb39946"),
    (18318342, "8da002e4809b62865df1cd83e1508e5eae377f51af8cc94b9e63f86637ec96bb"),
    (24011506, "2673cba362792fa224889c733a87455d8514c38f9868b789791069f11e3b46fa"),
)


def child_cpu():
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return usage.ru_utime + usage.ru_stime


def panel(work):
    source = subprocess.check_output(["git", "show", NATIVE], cwd=HERE)
    if hashlib.sha256(source).hexdigest() != "52c20890f4c920742e339c5c66e04b76b819604d913160ee8b63967e6e0aa341":
        raise ValueError("unexpected field implementation")
    (work / "native_v2.cpp").write_bytes(source)
    builds = {}
    for count in (1, 2, 4):
        builds[count] = work / f"walk{count}"
        subprocess.run(["clang++", "-O3", "-mcpu=native", "-std=c++20", f"-DCHAIN_COUNT={count}",
                        "-I", work, HERE / "walk.cpp", "-o", builds[count]], check=True)

    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["seed", "queries", "round", "position", "chains", "wall_ms", "cpu_ms", "stream_sha256"])
    rng = random.Random(20261124)
    for seed, (queries, expected) in enumerate(CASES):
        args = [str(seed), str(queries)]
        for exe in builds.values():
            with subprocess.Popen([exe, *args], stdout=subprocess.PIPE) as child:
                digest = hashlib.file_digest(child.stdout, "sha256").hexdigest()
                if child.wait() or digest != expected:
                    raise ValueError(f"public stream mismatch for {exe.name} seed {seed}")
        plan = list(itertools.permutations(builds))
        rng.shuffle(plan)
        for rnd, order in enumerate(plan):
            for pos, count in enumerate(order):
                cpu = child_cpu()
                start = time.perf_counter_ns()
                subprocess.run([builds[count], *args], stdout=subprocess.DEVNULL, check=True)
                wall_ms = (time.perf_counter_ns() - start) / 1e6
                writer.writerow([seed, queries, rnd, pos, count, wall_ms, (child_cpu()-cpu)*1000, expected])


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as directory:
        panel(Path(directory))
