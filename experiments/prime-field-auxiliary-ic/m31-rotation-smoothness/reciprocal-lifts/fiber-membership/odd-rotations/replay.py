"""Exercise exact rotation sets and time complete public coverage queries."""
import csv
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
from time import process_time_ns, perf_counter_ns

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here.parent))
from query import P, coverage, make_smooth_test, orbit_hits, odd_orbit_hits

rng = random.Random(31189)
words = [1, P-1, *[1 << i for i in range(31)], *[P ^ (1 << i) for i in range(31)]]
words.extend(rng.randrange(1,P) for _ in range(4096))
for x in words:
    observed = []
    odd_orbit_hits(x, observed.append)
    rotations = {(x << i) % P for i in range(31)}
    assert set(observed) == {v for v in rotations if v % 2} and len(observed) == x.bit_count()
for b in (89,211):
    smooth = make_smooth_test(b,"multiple")
    for x in words:
        assert orbit_hits(x,smooth) == odd_orbit_hits(x,smooth)

base = here.parents[1]
receipt = json.loads((base/"archive-overlap/result.json").read_text())
path = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/results/field31_s5_base0/public.json"
raw = subprocess.check_output(["git","show",f"{receipt['archive']}:{path}"], cwd=here)
assert hashlib.sha256(raw).hexdigest() == receipt["fixture_sha256"]
fixture = json.loads(raw)
expected = {row["bound"]:row["levels"] for row in json.loads((base/"bound-211/coverage.json").read_text())}
writer = csv.writer(sys.stdout,lineterminator="\n")
writer.writerow(("block","bound","method","calls","wall_ns","cpu_ns"))
for block in range(24):
    for bound in ((89,211) if block%2 == 0 else (211,89)):
        for method in (("multiple","odd") if block%4 < 2 else ("odd","multiple")):
            wall, cpu = perf_counter_ns(), process_time_ns()
            for _ in range(16):
                if coverage(fixture,bound,method) != expected[bound]:
                    raise ValueError("coverage mismatch")
            cpu = process_time_ns()-cpu
            writer.writerow((block,bound,method,16,perf_counter_ns()-wall,cpu))
