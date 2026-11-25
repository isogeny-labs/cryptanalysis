"""Check every lift mask and time complete census commands in balanced order."""
import csv
import hashlib
from itertools import permutations
from pathlib import Path
import subprocess
import sys
from time import perf_counter_ns

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from census import P, lift_masks

pairs, direct, shared = map(lambda path: str(Path(path).resolve()), sys.argv[1:])
reference = (root / "phases.csv").read_bytes()
selected = subprocess.check_output([pairs])
expected = []
for x in map(int, selected.splitlines()):
    a = lift_masks(x, 2)
    b = lift_masks(pow(x, -1, P), (P+1)//2)
    if a[0] != b[0]:
        raise ValueError("auxiliary transport mismatch")
    expected.append((x, *a, *b[1:]))
for helper in (direct, shared):
    output = subprocess.check_output([helper, "--masks"], input=selected)
    if [tuple(map(int, line.split())) for line in output.splitlines()] != expected:
        raise ValueError(f"mask mismatch in {helper}")

writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(("block", "arm", "complete_ns", "mask_process_ns", "sha256"))
for block, order in enumerate(permutations(("gmp", "direct", "shared"))):
    for arm in order:
        start = perf_counter_ns()
        mask_time = ""
        if arm == "gmp":
            result = subprocess.check_output([sys.executable, str(root / "census.py"),
                                              "--gmp", "--pair-generator", pairs])
        else:
            data = subprocess.check_output([pairs])
            mask_start = perf_counter_ns()
            result = subprocess.check_output([direct if arm == "direct" else shared], input=data)
            mask_time = perf_counter_ns() - mask_start
        elapsed = perf_counter_ns() - start
        if result != reference:
            raise ValueError(f"phase mismatch for {arm}")
        writer.writerow((block, arm, elapsed, mask_time, hashlib.sha256(result).hexdigest()))
