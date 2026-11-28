"""Run the frozen M31 basis-size screen with create-once raw reports."""
import csv
import hashlib
import json
import random
import resource
import runpy
import subprocess
import sys
from pathlib import Path
from time import perf_counter_ns

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
helpers = runpy.run_path(str(HERE.parent / "m31-full-rust-comparison/replay.py"))
fixture = json.loads(helpers["frozen"]("comparison/field31/auxiliary/public.json"))
curve = helpers["Curve"](fixture["p"], a4=fixture["a"], a6=fixture["b"])
binary = Path("/Volumes/SSD990/m31-integrated-screen-target/release/m31-fast")
assert binary.is_file()
assert fixture["Q"] == [988441464, 1643383878]
assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip().startswith("ed350380e")

cells = [(columns, seed) for columns in (128, 256, 384, 512, 768, 1024) for seed in range(3)]
random.Random(2026112732).shuffle(cells)
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(["position", "columns", "seed", "status", "exit_code", "scalar", "wall_ns",
                 "cpu_ns", "cold_ns", "index_ns", "online_ns", "queries", "relations",
                 "entries", "report_sha256"])
for position, (columns, seed) in enumerate(cells):
    cmd = [str(binary), "--qx", str(fixture["Q"][0]), "--qy", str(fixture["Q"][1]),
           "--seed", str(seed), "--columns", str(columns), "--summands", "2",
           "--method", "indexed", "--base", "interval", "--lanes", "64",
           "--max-queries", "4000000", "--max-ms", "5000"]
    child = resource.getrusage(resource.RUSAGE_CHILDREN)
    own = resource.getrusage(resource.RUSAGE_SELF)
    started = perf_counter_ns()
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True)
    wall = perf_counter_ns() - started
    after_child = resource.getrusage(resource.RUSAGE_CHILDREN)
    after_own = resource.getrusage(resource.RUSAGE_SELF)
    cpu = round(1e9 * (after_child.ru_utime - child.ru_utime + after_child.ru_stime - child.ru_stime
                       + after_own.ru_utime - own.ru_utime + after_own.ru_stime - own.ru_stime))
    (HERE / f"base-{columns}-seed-{seed}.json").open("xb").write(result.stdout)
    (HERE / f"base-{columns}-seed-{seed}.stderr").open("xb").write(result.stderr)
    data = json.loads(result.stdout) if result.stdout else {}
    status = data.get("status", "error")
    scalar = data.get("scalar")
    if status == "solved":
        assert result.returncode == 0 and scalar is not None
        assert curve.mul(scalar, tuple(fixture["P"])) == tuple(fixture["Q"])
    else:
        assert result.returncode != 0
    work = data.get("work") or {}
    writer.writerow([position, columns, seed, status, result.returncode, scalar, wall, cpu,
                     data.get("cold_to_report_ns"), data.get("pair_index_ns"),
                     data.get("online_ns"), work.get("queries"), work.get("relations"),
                     (data.get("setup_pair_counts") or {}).get("entries"),
                     hashlib.sha256(result.stdout).hexdigest()])
    sys.stdout.flush()
