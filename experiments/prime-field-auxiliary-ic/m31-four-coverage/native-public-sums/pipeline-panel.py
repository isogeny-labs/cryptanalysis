"""Run python3 pipeline-panel.py > pipeline-times.csv on a little-endian host.

Each arm regenerates the table and writes the full multiplicity vector in two
fresh processes. Streams and binaries may be in the OS cache. File close is
timed; disk durability, input-stream preparation and verification are excluded.
"""
import ast
from collections import Counter
import csv
import hashlib
from itertools import permutations
from pathlib import Path
import random
import resource
import struct
import subprocess
import sys
import tempfile
import time

SOURCE = Path(__file__).resolve().parent
ARMS = {
    "baseline": ("remainder", "1024", "std", "binary"),
    "hash": ("census", "paired-512-lanes4", "radix", "hash"),
    "filtered": ("census", "paired-512-lanes4", "radix", "filtered-prefix"),
}


def pack(words):
    return struct.pack(f"<{len(words)}I", *words)


def child_cpu():
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return usage.ru_utime + usage.ru_stime


def panel(work):
    for exe, source, flags in [("remainder", "census", ["-DM31_BASELINE_REMAINDER"]),
                               ("census", "census", []), ("lookup", "prefix-lookup", [])]:
        subprocess.run(["clang++", "-O3", "-std=c++20", "-mcpu=native", *flags,
                        SOURCE / (source + ".cpp"), "-o", work / exe], check=True)
    lean = (SOURCE.parent / "HoldoutMultiplicity.lean").read_text()
    points = ast.literal_eval(lean.split("def input : List Point := ", 1)[1].split("]", 1)[0] + "]")
    fixtures = {
        "basis": ((SOURCE / "basis.txt").read_bytes(), "94ea695bcce35285ed2dea298caeebc4c401fcf6c41931a65cba1700b3b2c0fb"),
        "holdout": ("".join(f"{x} {y}\n" for x, y in points).encode(), "f99708c1e0bc5df6447035fbc873300a496b20809aecc3d4279bc3aae6f146a9"),
    }
    cases = {}
    table, answers = work / "table", work / "counts"
    for fixture, (basis, digest) in fixtures.items():
        subprocess.run([work / "remainder", "1024", table, "std", "multiset"], input=basis,
                       stdout=subprocess.DEVNULL, check=True)
        data = table.read_bytes()
        table.unlink()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("unexpected reference table")
        keys = struct.unpack("<28033I", data)
        counts = Counter(keys)
        for seed in (2026112419, 2026112420):
            for mix in ("uniform", "half-planted"):
                rng = random.Random(seed)
                stream = [rng.randrange(2147483647) if mix == "uniform" or i % 2 == 0
                          else rng.choice(keys) for i in range(262144)]
                for n in (8192, 262144):
                    case = fixture, seed, mix, n
                    path = work / "-".join(map(str, case))
                    path.write_bytes(pack(stream[:n]))
                    cases[case] = path, pack([counts[q] for q in stream[:n]])
    plan = [(case, r, order) for case in cases for r, order in enumerate(permutations(ARMS))]
    random.Random(2026112421).shuffle(plan)
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["fixture", "seed", "mix", "queries", "round", "position", "arm", "wall_ns", "child_cpu_us"])
    for case, rnd, order in plan:
        basis, digest = fixtures[case[0]]
        queries, expected = cases[case]
        for pos, arm in enumerate(order):
            exe, generator, sort, mode = ARMS[arm]
            build = [work / exe, generator, table, sort, "multiset"]
            search = [work / "lookup", mode, table, queries, answers]
            before = child_cpu()
            start = time.perf_counter_ns()
            subprocess.run(build, input=basis, stdout=subprocess.DEVNULL, check=True)
            subprocess.run(search, stdout=subprocess.DEVNULL, check=True)
            elapsed = time.perf_counter_ns() - start
            cpu_us = round((child_cpu() - before) * 1e6)
            if hashlib.sha256(table.read_bytes()).hexdigest() != digest or answers.read_bytes() != expected:
                raise ValueError(f"incorrect results in {case} with {arm}")
            table.unlink()
            answers.unlink()
            writer.writerow([*case, rnd, pos, arm, elapsed, cpu_us])


if __name__ == "__main__":
    if sys.byteorder != "little":
        raise RuntimeError("fixture files use little-endian words")
    with tempfile.TemporaryDirectory() as directory:
        panel(Path(directory))
