"""Replay the coordinate-only comparison, measuring one build per fresh process in first mode."""
import argparse
import csv
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("native", type=Path)
parser.add_argument("single_unit", type=Path)
args = parser.parse_args()
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(["build", "mode", "round", "position", "method", "ns"])
for run in range(64):
    binaries = [("native", args.native), ("single-unit", args.single_unit)]
    if run % 4 >= 2:
        binaries.reverse()
    for build, binary in binaries:
        order = "oz" if run % 2 == 0 else "zo"
        command = [str(binary.resolve()), "coordinate-only"]
        modes = ["warm", "first"] if run % 4 in (0, 3) else ["first", "warm"]
        for mode in modes:
            if mode == "first":
                lines = [subprocess.check_output([*command, method, "first"], text=True).strip()
                         for method in order]
            else:
                lines = subprocess.check_output([*command, order], text=True).splitlines()
            rows = list(csv.reader(lines))
            if "".join(row[0] for row in rows) != order:
                raise ValueError(f"Unexpected output for {build}, round {run}")
            for position, (method, ns) in enumerate(rows):
                writer.writerow([build, mode, run, position, method, ns])
