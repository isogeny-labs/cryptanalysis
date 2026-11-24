"""Usage: python3 hash-panel.py > results.csv (requires a little-endian host)."""
import argparse
import ast
from collections import Counter
import csv
import hashlib
from itertools import permutations
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile

SOURCE = Path(__file__).resolve().parent
MODES = ("binary", "prefix", "hash")


def pack(words):
    return struct.pack(f"<{len(words)}I", *words)


def run(confirm):
    if sys.byteorder != "little":
        raise RuntimeError("fixture files use little-endian words")
    lean = (SOURCE.parent / "HoldoutMultiplicity.lean").read_text()
    points = ast.literal_eval(lean.split("def input : List Point := ", 1)[1].split("]", 1)[0] + "]")
    fixtures = {
        "basis": ((SOURCE / "basis.txt").read_bytes(),
                  "94ea695bcce35285ed2dea298caeebc4c401fcf6c41931a65cba1700b3b2c0fb"),
        "holdout": ("".join(f"{x} {y}\n" for x, y in points).encode(),
                    "f99708c1e0bc5df6447035fbc873300a496b20809aecc3d4279bc3aae6f146a9"),
    }
    with tempfile.TemporaryDirectory() as work:
        work = Path(work)
        for name in ["census", "prefix-lookup"]:
            subprocess.run(["clang++", "-O3", "-std=c++20", "-mcpu=native",
                            SOURCE / (name + ".cpp"), "-o", work / name], check=True)
        cases = {}
        for fixture, (basis, digest) in fixtures.items():
            table = work / fixture
            subprocess.run([work / "census", "paired-512-lanes4", table, "radix", "multiset"],
                           check=True, input=basis, stdout=subprocess.DEVNULL)
            data = table.read_bytes()
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError("unexpected fixture table")
            keys = struct.unpack("<28033I", data)
            counts = Counter(keys)
            for mix in ["uniform", "half-planted"]:
                rng = random.Random(2026112417 if confirm else 2026112414)
                stream = [rng.randrange(2147483647) if mix == "uniform" or i % 2 == 0
                          else rng.choice(keys) for i in range(262144)]
                for n in ([262144] if confirm else [512, 8192, 65536, 262144]):
                    path = work / f"{fixture}-{mix}-{n}"
                    qs = stream[:n]
                    path.write_bytes(pack(qs))
                    cases[fixture, mix, n] = path, pack([counts[q] for q in qs])
        orders = list(permutations(MODES)) * 2
        plan = [(case, r, order) for case in cases for r, order in enumerate(orders)]
        random.Random(2026112418 if confirm else 2026112416).shuffle(plan)
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(["panel", "fixture", "mix", "queries", "round", "position", "mode", "index_and_lookup_us"])
        for case, r, order in plan:
            path, expected = cases[case]
            for pos, mode in enumerate(order):
                result = work / "counts"
                us = subprocess.check_output([work / "prefix-lookup", mode, work / case[0], path, result])
                if result.read_bytes() != expected:
                    raise ValueError(f"incorrect multiplicity in {case} with {mode}")
                result.unlink()
                writer.writerow(["confirmation" if confirm else "initial", *case, r, pos, mode, us.decode().strip()])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm", action="store_true", help="repeat the largest query batch on a fresh stream")
    run(parser.parse_args().confirm)
