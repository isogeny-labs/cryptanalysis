"""Create-once diagnostic replay of the integrated coordinate-input M31 command."""
import csv
import hashlib
import json
import resource
import runpy
import subprocess
import sys
from pathlib import Path
from time import perf_counter_ns

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HELPERS = runpy.run_path(str(HERE.parent / "m31-full-rust-comparison/replay.py"))
fixture = json.loads(HELPERS["frozen"]("comparison/field31/auxiliary/public.json"))
Curve = HELPERS["Curve"]
curve = Curve(fixture["p"], a4=fixture["a"], a6=fixture["b"])
binary = Path("/Volumes/SSD990/m31-integrated-screen-target/release/m31-fast")
assert binary.is_file()
assert fixture["Q"] == [988441464, 1643383878]
assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip().startswith("ed350380e")

writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(["seed", "status", "exit_code", "scalar", "wall_ns", "cpu_ns",
                 "cold_ns", "base_ns", "preparation_ns", "index_ns", "online_ns",
                 "queries", "relations", "constructed_pairs", "entries", "lookups",
                 "group_replays", "stdout_sha256"])
for seed in range(3):
    cmd = [str(binary), "--qx", str(fixture["Q"][0]), "--qy", str(fixture["Q"][1]),
           "--seed", str(seed), "--columns", "256", "--summands", "2",
           "--method", "indexed", "--base", "interval", "--max-queries", "4000000",
           "--max-ms", "5000"]
    child = resource.getrusage(resource.RUSAGE_CHILDREN)
    own = resource.getrusage(resource.RUSAGE_SELF)
    started = perf_counter_ns()
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True)
    wall = perf_counter_ns() - started
    later_child = resource.getrusage(resource.RUSAGE_CHILDREN)
    later_own = resource.getrusage(resource.RUSAGE_SELF)
    cpu = round(1e9 * (later_child.ru_utime - child.ru_utime + later_child.ru_stime - child.ru_stime
                       + later_own.ru_utime - own.ru_utime + later_own.ru_stime - own.ru_stime))
    (HERE / f"seed-{seed}.json").open("xb").write(result.stdout)
    (HERE / f"seed-{seed}.stderr").open("xb").write(result.stderr)
    data = json.loads(result.stdout) if result.stdout else {}
    status = data.get("status", "error")
    scalar = data.get("scalar")
    if status == "solved":
        assert result.returncode == 0 and scalar is not None
        assert curve.mul(scalar, tuple(fixture["P"])) == tuple(fixture["Q"])
    else:
        assert result.returncode != 0
    stats = data.get("work", {})
    setup = data.get("setup_pair_counts") or {}
    online = data.get("online_pair_counts") or {}
    writer.writerow([seed, status, result.returncode, scalar, wall, cpu,
                     data.get("cold_to_report_ns"), data.get("base_construction_ns"),
                     data.get("group_preparation_ns"), data.get("pair_index_ns"),
                     data.get("online_ns"), stats.get("queries"), stats.get("relations"),
                     setup.get("constructed_pairs"), setup.get("entries"),
                     online.get("lookups"), online.get("group_replays"),
                     hashlib.sha256(result.stdout).hexdigest()])
    sys.stdout.flush()
