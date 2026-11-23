"""Recompute the two fixed public-basis sumsets and emit aggregate counts."""
from pathlib import Path
import argparse
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
REV = "efb9330c1ee7e30743b7674f686cccb49f1cb25e"
ARCHIVE = "experiments/prime-field-auxiliary-ic/snapshot/comparison"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--multiplicity", action="store_true")
args = parser.parse_args()
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    for name, member in [
        ("common.hpp", "common.hpp"),
        ("auxiliary.txt", "field31/auxiliary/public.txt"),
        ("plain.txt", "field31/plain/public.txt"),
    ]:
        (root / name).write_bytes(subprocess.check_output(
            ["git", "show", f"{REV}:{ARCHIVE}/{member}"], cwd=HERE))
    exe = root / "census"
    subprocess.run(["c++", "-std=c++20", "-O3", "-DFIELD_BITS=31", "-I", root,
                    HERE / "census.cpp", "-o", exe], check=True)
    subprocess.run([exe, root / "auxiliary.txt", root / "plain.txt"]
                   + (["--multiplicity"] if args.multiplicity else []), check=True)
