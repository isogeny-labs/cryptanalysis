"""Replay a published timing schedule against a locally built torus7-build binary."""
import argparse
import csv
import itertools
from pathlib import Path
import subprocess
import sys


def schedule(mode):
    groups = ["archive", "holdout", "fresh"]
    if mode == "single":
        orders = ["uxy", "xyu", "yux", "yxu", "xuy", "uyx"]
        for run in range(6):
            for terminal in range(32):
                for offset in range(3):
                    yield (groups[(offset + run + terminal) % 3], run, terminal,
                           orders[(run + terminal) % 6])
    elif mode == "fourth":
        for run in range(48):
            yield "fourth", run, run % 32, ["ux", "xu"][run % 2]
    else:
        orders = ["".join(p) for p in itertools.permutations("uxy")]
        for run in range(48):
            order = orders[run % 6 if run // 6 % 2 == 0 else 5 - run % 6]
            for offset in range(3):
                yield groups[(run + offset) % 3], run, run % 32, order


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("binary", type=Path)
parser.add_argument("mode", choices=["single", "stream", "fourth"])
args = parser.parse_args()
writer = csv.writer(sys.stdout, lineterminator="\n")
single = args.mode == "single"
writer.writerow(["group", "terminal", "round", "position", "method", "base", "twist", "ns"]
                if single else ["group", "rotation", "position", "method", "ns_per_pair"])
for group, run, terminal, order in schedule(args.mode):
    cmd = [str(args.binary.resolve()), "fiber-half", str(terminal), order]
    if single:
        cmd.append("single")
    if group != "archive":
        cmd.append(group)
    rows = list(csv.reader(subprocess.check_output(cmd, text=True).splitlines()))
    if "".join(row[0] for row in rows) != order:
        raise ValueError(f"Unexpected method order for {cmd}")
    for position, row in enumerate(rows):
        prefix = [group, terminal, run] if single else [group, run]
        writer.writerow([*prefix, position, *row])
