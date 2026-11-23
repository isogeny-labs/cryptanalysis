"""Measure the original GMP census and the complete native census side by side."""
import csv
import hashlib
from pathlib import Path
import subprocess
import sys
from time import perf_counter_ns

flat, masks = [str(Path(arg).resolve()) for arg in sys.argv[1:]]
root = Path(__file__).resolve().parents[1]
expected = (root / "phases.csv").read_bytes()
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(("block", "arm", "complete_ns", "phase_sha256"))
for block in range(8):
    for arm in (("gmp", "native") if block % 2 == 0 else ("native", "gmp")):
        start = perf_counter_ns()
        if arm == "gmp":
            result = subprocess.check_output([sys.executable, str(root / "census.py"), "--gmp"])
        else:
            selected = subprocess.check_output([flat])
            result = subprocess.check_output([masks], input=selected)
        elapsed = perf_counter_ns() - start
        if result != expected:
            raise ValueError(f"phase mismatch in {arm} block {block}")
        writer.writerow((block, arm, elapsed, hashlib.sha256(result).hexdigest()))
