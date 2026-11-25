"""Measure one owned pair of M31 tables per fresh process; write raw observations to stdout."""
import argparse
import csv
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("binary", type=Path)
parser.add_argument("panel", choices=["previous", "fresh"])
parser.add_argument("--register-bic", type=Path,
                    help="compare two binaries using the direct owned-table method")
parser.add_argument("--first-then-warm", action="store_true",
                    help="measure first call and median of 33 following calls in each process")
args = parser.parse_args()
if args.first_then_warm and not args.register_bic:
    parser.error("--first-then-warm requires --register-bic")
start = 385 if args.panel == "previous" else 449
first = 340921998
previous, current = 2, first
terminals = []
seen = set()
for power in range(1, start + 63):
    if power % 2:
        if current in seen:
            raise ValueError(f"Repeated terminal at power {power}")
        seen.add(current)
        if power >= start:
            terminals.append(current)
    previous, current = current, (first * current - previous) % (2**31 - 1)
assert len(terminals) == 32
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(["round", "terminal", "position", "method", "ns"] + (["warm_ns"] if args.first_then_warm else []))
for run in range(12):
    for step in range(32):
        index = (13 * step + 7 * run) % 32
        terminal = terminals[index]
        order = ["control", "bic"] if args.register_bic else ["direct", "fixed"]
        if (index + run) % 2:
            order.reverse()
        for position, method in enumerate(order):
            binary = args.register_bic if method == "bic" else args.binary
            implementation = "direct" if args.register_bic else method
            cmd = [str(binary.resolve()), "first-table", str(terminal), implementation]
            if args.first_then_warm:
                cmd = [str(binary.resolve()), "first-then-warm", str(terminal)]
            ns = list(map(int, subprocess.check_output(cmd, text=True).strip().split(",")))
            if len(ns) != (2 if args.first_then_warm else 1) or min(ns) <= 0:
                raise ValueError(f"Invalid timings from {cmd}")
            writer.writerow([run, terminal, position, method, *ns])
