"""Paired build timings with independently regenerated compact reference tables."""
import argparse
import csv
import shutil
from pathlib import Path
import random
import runpy
import subprocess
import sys
import tempfile

source = Path(__file__).resolve().parent.parent / "m31-public-pair-build"
reference = runpy.run_path(str(source / "replay.py"))

def replay(directory, implementation="cpp"):
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
    blocks = [(basis, r) for basis in reference["DIGESTS"] for r in range(24)]
    random.Random(112427).shuffle(blocks)
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["basis", "round", "position", "rows", "build_ns"])
    for basis, r in blocks:
        order = ("flat", "reflected") if r % 2 else ("reflected", "flat")
        for pos, label in enumerate(order):
            command = (["./target/release/public-row-benchmark", basis, label]
                       if implementation == "rust" else [f"./{label}", basis, "compact"])
            ns = subprocess.check_output(command + [f"{basis}-compact.bin"], cwd=directory)
            writer.writerow([basis, r, pos, label, int(ns)])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--implementation", choices=["cpp", "rust"], default="cpp")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        replay(Path(tmp), args.implementation)
