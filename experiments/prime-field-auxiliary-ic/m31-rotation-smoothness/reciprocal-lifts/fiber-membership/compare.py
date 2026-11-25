"""Compare fresh-process coverage queries at both bounds in all six arm orders."""
import csv
import hashlib
from itertools import permutations
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter_ns


here = Path(__file__).resolve().parent
receipt = json.loads((here.parent/"archive-overlap/result.json").read_text())
path = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/results/field31_s5_base0/public.json"
raw = subprocess.check_output(["git","show",f"{receipt['archive']}:{path}"], cwd=here)
assert hashlib.sha256(raw).hexdigest() == receipt["fixture_sha256"]
expected = {row["bound"]:row["levels"] for row in json.loads((here.parent/"bound-211/coverage.json").read_text())}
writer = csv.writer(sys.stdout,lineterminator="\n")
writer.writerow(("block","bound","arm","process_wall_ns"))
with TemporaryDirectory() as tmp:
    fixture = Path(tmp)/"public.json"
    fixture.write_bytes(raw)
    for i, order in enumerate(permutations(("index","trial","multiple"))):
        for bound in ((89,211) if i%2==0 else (211,89)):
            for method in order:
                cmd = [sys.executable,str(here/"query.py"),str(fixture),str(bound),"--method",method]
                if method == "index":
                    cmd += ["--helper",str(Path(sys.argv[1])/f"pairs{bound}")]
                start = perf_counter_ns()
                out = subprocess.check_output(cmd)
                elapsed = perf_counter_ns()-start
                assert json.loads(out) == expected[bound]
                writer.writerow((i,bound,method,elapsed))
