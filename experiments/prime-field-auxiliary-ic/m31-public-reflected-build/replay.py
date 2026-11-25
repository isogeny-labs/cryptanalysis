"""Paired build timings with independently regenerated compact reference tables."""
import argparse
import csv
import shutil
import resource
from time import perf_counter_ns
from pathlib import Path
import random
import runpy
import subprocess
import sys
import tempfile

source = Path(__file__).resolve().parent.parent / "m31-public-pair-build"
reference = runpy.run_path(str(source / "replay.py"))

def replay(directory, implementation="cpp", check_only=False, cold=False):
    if implementation == "rust":
        crate = "crates/prime-field-auxiliary-ic"
        repo = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=source, text=True).strip()
        archive = subprocess.check_output(["git", "archive", "HEAD", crate], cwd=repo)
        subprocess.run(["tar", "-xf", "-", "-C", str(directory)], input=archive, check=True)
        (directory / "src").mkdir()
        shutil.copyfile(Path(__file__).with_name("build.rs"), directory / "src/main.rs")
        (directory / "Cargo.toml").write_text(
            '[package]\nname = "public-row-benchmark"\nversion = "0.1.0"\nedition = "2021"\n'
            '[dependencies]\nprime-field-auxiliary-ic = { path = "crates/prime-field-auxiliary-ic" }\n')
        subprocess.run(["cargo", "build", "--release", "--offline"], cwd=directory, check=True)

    if sys.byteorder != "little":
        raise RuntimeError("The reference table format requires little endian")
    (directory / "common.hpp").write_bytes(reference["frozen"]("common.hpp"))
    reference["collision_control"]()
    for basis in reference["DIGESTS"]:
        reference["references"](directory, basis)
    if implementation == "cpp":
        for label, flags in [("flat", []), ("reflected", ["-DM31_REFLECT_ROWS"])]:
            subprocess.run(["c++", "-std=c++17", "-O3", "-DFIELD_BITS=31", "-DM31_FLAT_INDEX", *flags,
                            "-I", str(directory), str(source / "build.cpp"), "-o", label],
                           cwd=directory, check=True)
    if implementation == "rust":
        points = [(1, 814455902), (159715794, 2076807678)] * 250
        (directory / "collisions").write_text("".join(f"{x} {y}\n" for x, y in points))
        entries = reference["signed_pair_entries"](points, 2**31 - 1)
        blob = reference["encode"]((key // 2, value) for key, value in sorted(entries.items()) if key % 2 == 0)
        (directory / "collisions.bin").write_bytes(blob)
        for mode in ("flat", "reflected"):
            subprocess.run(["./target/release/public-row-benchmark", "collisions", mode,
                            "collisions.bin"], cwd=directory, check=True, stdout=subprocess.DEVNULL)
        damaged = bytearray(blob)
        damaged[4] ^= 1
        (directory / "wrong-payload.bin").write_bytes(damaged)
        (directory / "truncated.bin").write_bytes(blob[:-1])
        (directory / "off-curve").write_text("0 0\n" + "".join(f"{x} {y}\n" for x, y in points[1:]))
        (directory / "short-input").write_text("1 814455902\n")
        for mode in ("flat", "reflected"):
            for input_name, ref_name in [("collisions", "wrong-payload.bin"),
                                         ("collisions", "truncated.bin"),
                                         ("off-curve", "collisions.bin"),
                                         ("short-input", "collisions.bin")]:
                result = subprocess.run(["./target/release/public-row-benchmark", input_name,
                                         mode, ref_name], cwd=directory, capture_output=True)
                if result.returncode != 1:
                    raise AssertionError(f"Expected checked rejection for {mode}/{input_name}/{ref_name}: {result.returncode}")
    if check_only:
        for basis in reference["DIGESTS"]:
            for mode in ("flat", "reflected"):
                command = (["./target/release/public-row-benchmark", basis, mode]
                           if implementation == "rust" else [f"./{mode}", basis, "compact"])
                subprocess.run(command + [f"{basis}-compact.bin"], cwd=directory,
                               check=True, stdout=subprocess.DEVNULL)
        return
    blocks = [(basis, r) for basis in reference["DIGESTS"] for r in range(24)]
    random.Random(112427).shuffle(blocks)
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["basis", "round", "position", "rows", "build_ns"] +
                    (["process_wall_ns", "process_cpu_ns"] if cold else []))
    for basis, r in blocks:
        order = ("flat", "reflected") if r % 2 else ("reflected", "flat")
        for pos, label in enumerate(order):
            command = (["./target/release/public-row-benchmark", basis, label]
                       if implementation == "rust" else [f"./{label}", basis, "compact"])
            before = resource.getrusage(resource.RUSAGE_CHILDREN)
            started = perf_counter_ns()
            ns = subprocess.check_output(command + [f"{basis}-compact.bin"], cwd=directory)
            elapsed = perf_counter_ns() - started
            after = resource.getrusage(resource.RUSAGE_CHILDREN)
            cpu_ns = round(((after.ru_utime - before.ru_utime) +
                            (after.ru_stime - before.ru_stime)) * 1e9)
            writer.writerow([basis, r, pos, label, int(ns)] +
                            ([elapsed, cpu_ns] if cold else []))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--implementation", choices=["cpp", "rust"], default="cpp")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--cold", action="store_true", help="record whole fresh-process wall and CPU time")
    args = parser.parse_args()
    if args.cold and args.check_only:
        parser.error("--cold requires timing collection")
    with tempfile.TemporaryDirectory() as tmp:
        replay(Path(tmp), args.implementation, args.check_only, args.cold)
