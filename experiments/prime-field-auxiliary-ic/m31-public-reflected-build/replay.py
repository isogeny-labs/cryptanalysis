"""Paired build timings with independently regenerated compact reference tables."""
import csv
from pathlib import Path
import random
import runpy
import subprocess
import sys
import tempfile

source = Path(__file__).resolve().parent.parent / "m31-public-pair-build"
reference = runpy.run_path(str(source / "replay.py"))

def replay(directory):
    if sys.byteorder != "little":
        raise RuntimeError("The reference table format requires little endian")
    (directory / "common.hpp").write_bytes(reference["frozen"]("common.hpp"))
    reference["collision_control"]()
    for basis in reference["DIGESTS"]:
        reference["references"](directory, basis)
    for label, flags in [("flat", []), ("reflected", ["-DM31_REFLECT_ROWS"])]:
        subprocess.run(["c++", "-std=c++17", "-O3", "-DFIELD_BITS=31", "-DM31_FLAT_INDEX", *flags,
                        "-I", str(directory), str(source / "build.cpp"), "-o", label],
                       cwd=directory, check=True)
    blocks = [(basis, r) for basis in reference["DIGESTS"] for r in range(24)]
    random.Random(112427).shuffle(blocks)
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["basis", "round", "position", "rows", "build_ns"])
    for basis, r in blocks:
        order = ("flat", "reflected") if r % 2 else ("reflected", "flat")
        for pos, label in enumerate(order):
            ns = subprocess.check_output([f"./{label}", basis, "compact",
                                          f"{basis}-compact.bin"], cwd=directory)
            writer.writerow([basis, r, pos, label, int(ns)])

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        replay(Path(tmp))
