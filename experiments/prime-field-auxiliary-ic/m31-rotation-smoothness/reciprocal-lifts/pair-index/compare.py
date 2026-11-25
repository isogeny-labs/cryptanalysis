"""Fresh-process timings for complete bound-89 census runs."""
import csv
import hashlib
import subprocess
import sys
from itertools import permutations
from pathlib import Path
from time import perf_counter_ns

base, reserved, flat, masks = [str(Path(p).resolve()) for p in sys.argv[1:]]
helpers = {"base": base, "reserved": reserved, "flat": flat}
expected = (Path(__file__).resolve().parents[1] / "phases.csv").read_bytes()
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(("block", "arm", "pairs_ns", "complete_ns", "phase_sha256"))
for block, order in enumerate(permutations(helpers)):
    for arm in order:
        start = perf_counter_ns()
        selected = subprocess.check_output([helpers[arm]])
        generated = perf_counter_ns()
        result = subprocess.check_output([masks], input=selected)
        finished = perf_counter_ns()
        if result != expected:
            raise ValueError(f"{arm} failed phase replay in block {block}")
        writer.writerow((block, arm, generated-start, finished-start, hashlib.sha256(result).hexdigest()))
