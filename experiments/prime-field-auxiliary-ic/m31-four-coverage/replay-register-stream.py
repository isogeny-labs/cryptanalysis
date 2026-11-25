"""Compare the register-BIC and control binaries on complete warmed table pairs."""
import argparse
import csv
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("control", type=Path)
parser.add_argument("bic", type=Path)
parser.add_argument("--allocation", action="store_true",
                    help="compare fresh and reused buffers with the same vector-table path")
args = parser.parse_args()
panels = ["archive", "holdout", "fresh", "fourth"]
writer = csv.writer(sys.stdout, lineterminator="\n")
columns = ["round", "panel", "rotation", "position", "binary"]
writer.writerow(columns + (["order", "buffer"] if args.allocation else []) + ["ns_per_pair"])
for run in range(48):
    for step in range(4):
        index = (step + run) % 4
        panel = panels[index]
        methods = ["control", "bic"]
        if (run + index) % 2:
            methods.reverse()
        for position, arm in enumerate(methods):
            binary = getattr(args, arm).resolve()
            order = ("ar" if (run // 2 + index) % 2 == 0 else "ra") if args.allocation else "x"
            cmd = [str(binary), "fiber-half", str(run % 32), order]
            if panel != "archive":
                cmd.append(panel)
            rows = list(csv.reader(subprocess.check_output(cmd, text=True).splitlines()))
            if "".join(row[0] for row in rows) != order:
                raise ValueError(f"Unexpected output from {cmd}")
            for method, ns in rows:
                if float(ns) <= 0:
                    raise ValueError(f"Invalid timing from {cmd}")
                extra = [order, method] if args.allocation else []
                writer.writerow([run, panel, run % 32, position, arm, *extra, ns])
