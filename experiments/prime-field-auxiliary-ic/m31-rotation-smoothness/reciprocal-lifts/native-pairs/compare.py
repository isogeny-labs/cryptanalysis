"""Run six cold paired comparisons on the bound-89 census."""
import csv
import hashlib
import subprocess
import sys
import time
from itertools import permutations
from pathlib import Path

root = Path(__file__).resolve().parents[1]
helpers = dict(zip(("carry", "recompute"), (str(Path(p).resolve()) for p in sys.argv[1:]), strict=True))
expected = (root / "phases.csv").read_bytes()
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(("block", "arm", "wall_s", "sha256"))

for block, order in enumerate(permutations(("gmp", "carry", "recompute"))):
    for arm in order:
        argv = [sys.executable, str(root / "census.py"), "--gmp"]
        if arm in helpers:
            argv.extend(["--pair-generator", helpers[arm]])
        start = time.perf_counter()
        output = subprocess.check_output(argv)
        elapsed = time.perf_counter() - start
        if output != expected:
            raise ValueError(f"output mismatch on {arm} in block {block}")
        writer.writerow((block, arm, elapsed, hashlib.sha256(output).hexdigest()))
