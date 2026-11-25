"""Repeat just the two native mask processes on identical frozen input."""
import csv
from pathlib import Path
import subprocess
import sys
from time import perf_counter_ns

pairs, direct, shared = [str(Path(arg).resolve()) for arg in sys.argv[1:]]
data = subprocess.check_output([pairs])
reference = (Path(__file__).resolve().parents[1] / 'phases.csv').read_bytes()
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(("round", "direct_ns", "shared_ns"))
for i in range(24):
    times = []
    for arm in ((direct, shared) if i % 2 == 0 else (shared, direct)):
        start = perf_counter_ns()
        result = subprocess.check_output([arm], input=data)
        times.append(perf_counter_ns()-start)
        if result != reference:
            raise ValueError("phase mismatch")
    writer.writerow((i, *(times if i % 2 == 0 else reversed(times))))
