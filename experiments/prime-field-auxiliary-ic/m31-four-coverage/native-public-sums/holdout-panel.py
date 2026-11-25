"""Run from any directory with python3 holdout-panel.py /path/to/census > times.csv."""
import ast
import csv
import hashlib
import itertools
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile
from collections import Counter

# SHA-256 of Lean's M31HoldoutMultiplicity.coordinates.mergeSort encoded as LE u32.
EXPECTED = "f99708c1e0bc5df6447035fbc873300a496b20809aecc3d4279bc3aae6f146a9"

def main(executable):
    source = (Path(__file__).resolve().parent.parent / "HoldoutMultiplicity.lean").read_text()
    points = ast.literal_eval(source.split("def input : List Point := ", 1)[1].split("]", 1)[0] + "]")
    doubles = ast.literal_eval(source.split("def repeated : List Nat := ", 1)[1].split("]", 1)[0] + "]")
    basis = "".join(f"{x} {y}\n" for x, y in points).encode()
    arms = list(itertools.product(["1024", "paired-512"], ["std", "radix"]))
    orders = list(itertools.permutations(arms))
    random.Random(2026112406).shuffle(orders)
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["round", "position", "generator", "sort", "generation_ms", "sorted_table_ms"])
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "table.bin"
        strict = subprocess.run([executable, "paired-512", output, "radix"], input=basis)
        if strict.returncode != 3 or output.exists():
            raise RuntimeError("fixture with duplicates must fail the original uniqueness check")
        for rnd, order in enumerate(orders):
            for pos, (generator, sort) in enumerate(order):
                timings = subprocess.check_output(
                    [executable, generator, output, sort, "multiset"], input=basis
                )
                data = output.read_bytes()
                output.unlink()
                if hashlib.sha256(data).hexdigest() != EXPECTED:
                    raise ValueError("table differs from the independent Lean enumeration")
                counts = Counter(struct.unpack("<28033I", data))
                if Counter(counts.values()) != {1: 28007, 2: 13} or sorted(
                    key for key, count in counts.items() if count == 2
                ) != doubles:
                    raise ValueError("holdout multiplicity mismatch")
                generation, total = timings.decode().strip().split(",")
                writer.writerow([rnd, pos, generator, sort, generation, total])

if __name__ == "__main__":
    main(str(Path(sys.argv[1]).resolve()))
