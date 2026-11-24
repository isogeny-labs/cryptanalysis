"""Measure one owned pair of M31 tables per fresh process; write raw observations to stdout."""
import argparse
import csv
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("binary", type=Path)
parser.add_argument("panel", choices=["previous", "fresh"])
args = parser.parse_args()
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
writer.writerow(["round", "terminal", "position", "method", "ns"])
for run in range(12):
    for step in range(32):
        index = (13 * step + 7 * run) % 32
        terminal = terminals[index]
        order = ["direct", "fixed"]
        if (index + run) % 2:
            order.reverse()
        for position, method in enumerate(order):
            cmd = [str(args.binary.resolve()), "first-table", str(terminal), method]
            ns = int(subprocess.check_output(cmd, text=True))
            writer.writerow([run, terminal, position, method, ns])
