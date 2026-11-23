"""Run with python3 bench_census.py on an ARM64 host with Clang and LTO support.

Each row is a fresh process. Timing includes launch and reading its output,
and excludes compilation and the byte-for-byte check against population.txt.
"""
import itertools
from pathlib import Path
import platform
from statistics import median
import subprocess
import tempfile
import time


HERE = Path(__file__).resolve().parent
MODES = ("scalar", "batch", "batch_lto", "explicit_lto")


def compile_census(directory, mode):
    binary = directory / mode
    flags = ["-O3", "-mcpu=native"]
    if mode in ("batch_lto", "explicit_lto"):
        flags.append("-flto")
    objects = []
    if mode == "explicit_lto":
        flags.append("-DM31_EXPLICIT_CENSUS")
    elif mode != "scalar":
        product = directory / (mode + ".o")
        subprocess.run(["clang", *flags, "-c", HERE.parent / "m31-native-product/product.c",
                        "-o", product], check=True)
        flags.append("-DM31_BATCH_CENSUS")
        objects.append(product)
    subprocess.run(["clang++", *flags, "-std=c++17", HERE / "census.cpp", *objects,
                    "-o", binary], check=True)
    return binary


def measure(binary, expected):
    start = time.perf_counter_ns()
    output = subprocess.check_output([binary])
    duration = time.perf_counter_ns() - start
    if output != expected:
        raise ValueError(f"{binary.name} disagrees with population.txt")
    return duration


def main():
    expected = (HERE / "population.txt").read_bytes()
    print(platform.platform(), platform.machine())
    print(subprocess.check_output(["clang", "--version"], text=True).splitlines()[0])
    with tempfile.TemporaryDirectory() as directory:
        binaries = {mode: compile_census(Path(directory), mode) for mode in MODES}
        for binary in binaries.values():
            measure(binary, expected)
        print("round", "order", *(m + "_ns" for m in MODES), sep=",")
        rows = []
        for number, order in enumerate(itertools.permutations(MODES), start=1):
            row = {mode: measure(binaries[mode], expected) for mode in order}
            rows.append(row)
            print(number, "/".join(order), *(row[m] for m in MODES), sep=",")
        for mode in ("scalar", "batch", "explicit_lto"):
            ratio = median(row[mode] / row["batch_lto"] for row in rows)
            print(f"Median paired {mode}/batch_lto wall time = {ratio:.4f}")


if __name__ == "__main__":
    main()
