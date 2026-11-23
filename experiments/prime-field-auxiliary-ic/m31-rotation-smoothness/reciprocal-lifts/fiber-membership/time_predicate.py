"""Repeated in-process coverage calls, charging predicate construction on every call."""
import csv
import json
from pathlib import Path
import subprocess
import sys
from time import process_time_ns

from query import coverage

here = Path(__file__).resolve().parent
receipt = json.loads((here.parent/"archive-overlap/result.json").read_text())
path = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/results/field31_s5_base0/public.json"
fixture = json.loads(subprocess.check_output(["git","show",f"{receipt['archive']}:{path}"], cwd=here))
expected = {row["bound"]:row["levels"] for row in json.loads((here.parent/"bound-211/coverage.json").read_text())}
writer = csv.writer(sys.stdout,lineterminator="\n")
writer.writerow(("block","bound","method","calls","cpu_ns"))
for block in range(12):
    for bound in ((89,211) if block % 2 == 0 else (211,89)):
        for method in (("trial","multiple") if block % 4 < 2 else ("multiple","trial")):
            start = process_time_ns()
            for _ in range(16):
                answer = coverage(fixture,bound,method)
                if answer != expected[bound]:
                    raise ValueError("coverage mismatch")
            writer.writerow((block,bound,method,16,process_time_ns()-start))
