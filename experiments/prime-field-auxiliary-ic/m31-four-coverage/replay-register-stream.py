"""Compare the register-BIC and control binaries on complete warmed table pairs."""
import argparse
import csv
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("control", type=Path)
parser.add_argument("bic", type=Path)
args = parser.parse_args()
panels = ["archive", "holdout", "fresh", "fourth"]
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(["round", "panel", "rotation", "position", "binary", "ns_per_pair"])
for run in range(48):
    for step in range(4):
        index = (step + run) % 4
        panel = panels[index]
        methods = ["control", "bic"]
        if (run + index) % 2:
            methods.reverse()
        for position, arm in enumerate(methods):
            binary = getattr(args, arm).resolve()
            cmd = [str(binary), "fiber-half", str(run % 32), "x"]
            if panel != "archive":
                cmd.append(panel)
            method, ns = subprocess.check_output(cmd, text=True).strip().split(",")
            if method != "x" or float(ns) <= 0:
                raise ValueError(f"Unexpected output from {cmd}")
            writer.writerow([run, panel, run % 32, position, arm, ns])
