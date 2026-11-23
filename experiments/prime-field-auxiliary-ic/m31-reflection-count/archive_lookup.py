"""Audit the coordinate lookup's workload identity using public archival records."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REV = "efb9330c1"
BASE = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized"
FIXTURE = "results/field31_s5_base0"
def read(path):
    return subprocess.check_output(["git", "show", f"{REV}:{BASE}/{path}"], cwd=HERE)

def result(path):
    return json.loads(read(f"{FIXTURE}/{path}"))

source_hash = hashlib.sha256(read("native_v2.cpp")).hexdigest()
public = result("public.json")
p = public["public"]["p"]
points = public["factor_base"]
xs = set(public["structured_roots"])
coordinates = {x for x, _ in points}
assert p == 2147483647 and len(xs) == 32 and len(coordinates) == len(points) == 17
assert public["public"]["a"] == 2 and public["public"]["b"] == 14
assert coordinates < xs
chain = read(f"{FIXTURE}/chain.txt").decode().splitlines()
assert int(chain[2].split()[0]) == len(points)
assert [list(map(int, line.split())) for line in chain[3:3+len(points)]] == points

# Prior positive-sign trials on negative-sign rows could skip the map if R = F[i].
# That would require the signed second point to equal 2F[i]. Rule out its abscissa.
for x, y in points:
    assert (y*y - x**3 - 2*x - 14) % p == 0 and y % p != 0
    slope = (3*x*x + 2) * pow(2*y, -1, p) % p
    assert (slope*slope - 2*x) % p not in coordinates

print("seed,outer_queries,recorded_rows,duplicate_rows,successful_lookups,documented_minimum_misses,minimum_total_lookups")
for seed in range(3):
    stem = f"v2_batch_seed{seed}"
    row = result(f"{stem}.audited.json")
    relations = [json.loads(line) for line in read(f"{FIXTURE}/{stem}.relations.jsonl").splitlines()]
    assert row["source_sha256"] == source_hash and row["seed"] == seed and row["label"] == "v2_batch"
    assert len(relations) == row["relations"] == row["audit"]["verified_relations"]
    assert all(r["si"] in (-1,1) and r["sj"] in (-1,1)
               and 0 <= r["i"] < len(points) and 0 <= r["j"] < len(points) for r in relations)
    hits = row["relations"] + row["duplicate_relations_skipped"]
    misses = sum(r["si"] == -1 for r in relations)
    print(f'{seed},{row["queries"]},{len(relations)},{row["duplicate_relations_skipped"]},{hits},{misses},{hits+misses}')
