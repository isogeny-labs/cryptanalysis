"""Frozen public M31 development comparison of exact pair x lookups."""
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
curve_api = runpy.run_path(str(HERE.parent / "m31-full-rust-comparison/replay.py"))
fixture = json.loads(curve_api["frozen"]("comparison/field31/auxiliary/public.json"))
curve = curve_api["Curve"](fixture["p"], a4=fixture["a"], a6=fixture["b"])
qx, qy = fixture["Q"]
workers = {
    "control": Path("/Volumes/SSD990/m31-bitmap-control-target/release/m31-fast"),
    "bitmap": Path("/Volumes/SSD990/m31-bitmap-candidate-target/release/m31-fast"),
}
for path in workers.values():
    assert path.is_file(), path

writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(("columns", "seed", "position", "arm", "status", "scalar", "wall_ns",
                 "cpu_ns", "cold_ns", "index_ns", "online_ns", "queries", "relations",
                 "entries", "stdout_sha256", "binary_sha256"))
for columns in (384, 768):
    for seed in range(3):
        matched = None
        for position, arm in enumerate(("control", "bitmap") if seed % 2 else ("bitmap", "control")):
            cmd = [str(workers[arm]), "--qx", str(qx), "--qy", str(qy),
                   "--seed", str(seed), "--columns", str(columns), "--summands", "2",
                   "--method", "indexed", "--base", "interval", "--lanes", "64",
                   "--max-queries", "4000000", "--max-ms", "5000"]
            before_child = resource.getrusage(resource.RUSAGE_CHILDREN)
            before_self = resource.getrusage(resource.RUSAGE_SELF)
            started = perf_counter_ns()
            run = subprocess.run(cmd, cwd=ROOT, capture_output=True, timeout=20)
            data = json.loads(run.stdout)
            wall_ns = perf_counter_ns() - started
            after_child = resource.getrusage(resource.RUSAGE_CHILDREN)
            after_self = resource.getrusage(resource.RUSAGE_SELF)
            cpu_ns = round(1e9 * sum((after_child.ru_utime - before_child.ru_utime,
                                      after_child.ru_stime - before_child.ru_stime,
                                      after_self.ru_utime - before_self.ru_utime,
                                      after_self.ru_stime - before_self.ru_stime)))
            assert run.returncode == 0 and data["status"] == "solved", run.stderr
            assert curve.mul(data["scalar"], tuple(fixture["P"])) == (qx, qy)
            identity = (data["base_points"], data["scalar"], data["certificate"],
                        data["work"], data["setup_pair_counts"], data["online_pair_counts"])
            if matched is not None:
                assert identity == matched, (columns, seed)
            matched = identity
            (HERE / f"bitmap-b{columns}-s{seed}-{arm}.json").write_bytes(run.stdout)
            writer.writerow((columns, seed, position, arm, data["status"], data["scalar"],
                             wall_ns, cpu_ns, data["cold_to_report_ns"], data["pair_index_ns"],
                             data["online_ns"], data["work"]["queries"], data["work"]["relations"],
                             data["setup_pair_counts"]["entries"],
                             hashlib.sha256(run.stdout).hexdigest(),
                             hashlib.sha256(workers[arm].read_bytes()).hexdigest()))
            sys.stdout.flush()
