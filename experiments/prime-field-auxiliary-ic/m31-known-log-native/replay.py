"""Cold public-target development panel for the known-log two-sum control."""
import csv
import hashlib
import json
import resource
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path
from time import perf_counter_ns

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
api = runpy.run_path(str(HERE.parent / "m31-full-rust-comparison/replay.py"))
curve = api["Curve"](2147483647, a4=2, a6=14)
g = (1, 814455902)
q = (988441464, 1643383878)
known = Path("/Volumes/SSD990/m31-known-log-target/release/m31-known-log-control")
ic = Path("/Volumes/SSD990/m31-bitmap-tuned-target/release/m31-fast")
assert known.is_file() and ic.is_file()
labels = ("known128", "known192", "known256", "known384", "ic384", "rho")
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(("seed", "position", "arm", "status", "exit_code", "scalar", "wall_ns",
                 "cpu_ns", "cold_ns", "base_ns", "index_ns", "online_ns", "queries_or_steps",
                 "entries", "report_sha256", "binary_sha256"))
with tempfile.TemporaryDirectory(prefix="m31-known-log-") as td:
    tmp = Path(td)
    (tmp / "common.hpp").write_bytes(api["frozen"]("comparison/common.hpp"))
    (tmp / "compare_rho.cpp").write_bytes(api["frozen"]("comparison/compare_rho.cpp"))
    rho = tmp / "compare_rho"
    subprocess.run(["c++", "-std=c++17", "-O3", "-DFIELD_BITS=31",
                    str(tmp / "compare_rho.cpp"), "-o", str(rho)], check=True)
    for seed in range(3):
        order = labels[seed:] + labels[:seed]
        for position, arm in enumerate(order):
            if arm == "rho":
                workdir = tmp / f"s{seed}"
                workdir.mkdir()
                (workdir / "public.txt").write_text(
                    f"2147483647 2147505293 2 14\n1 814455902 {q[0]} {q[1]}\n0\n")
                binary = rho
                cmd = [str(rho), str(seed)]
            elif arm == "ic384":
                workdir = ROOT
                binary = ic
                cmd = [str(ic), "--qx", str(q[0]), "--qy", str(q[1]), "--seed", str(seed),
                       "--columns", "384", "--summands", "2", "--method", "indexed",
                       "--base", "interval", "--lanes", "64", "--max-queries", "4000000",
                       "--max-ms", "5000"]
            else:
                workdir = ROOT
                binary = known
                cmd = [str(known), "--qx", str(q[0]), "--qy", str(q[1]), "--seed", str(seed),
                       "--columns", arm.removeprefix("known")]
            before_child = resource.getrusage(resource.RUSAGE_CHILDREN)
            before_self = resource.getrusage(resource.RUSAGE_SELF)
            started = perf_counter_ns()
            try:
                result = subprocess.run(cmd, cwd=workdir, capture_output=True, timeout=20)
                stdout, stderr, code = result.stdout, result.stderr, result.returncode
                timed_out = False
            except subprocess.TimeoutExpired as exc:
                stdout, stderr, code = exc.stdout or b"", exc.stderr or b"", None
                timed_out = True
            data = json.loads(stdout) if stdout and arm != "rho" else {}
            if arm == "rho":
                metrics = workdir / "metrics.json"
                data = json.loads(metrics.read_text()) if metrics.exists() else {}
                scalar = data.get("recovered")
                status = "timed_out" if timed_out else ("solved" if code == 0 and scalar is not None else "error")
                cold = base_ns = index_ns = online_ns = entries = None
                queries = data.get("walk_steps")
            else:
                scalar = data.get("scalar")
                status = "timed_out" if timed_out else data.get("status", "error")
                cold = data.get("cold_to_report_ns")
                base_ns = data.get("base_ns", data.get("base_construction_ns"))
                index_ns = data.get("index_ns", data.get("pair_index_ns"))
                online_ns = data.get("online_ns")
                entries = data.get("entries", (data.get("setup_pair_counts") or {}).get("entries"))
                queries = data.get("queries", (data.get("work") or {}).get("queries"))
            if status == "solved":
                assert code == 0 and scalar is not None
                assert curve.mul(scalar, g) == q
            elif status == "timed_out":
                assert code is None
            else:
                assert code != 0 or status == "incomplete"
            wall_ns = perf_counter_ns() - started
            after_child = resource.getrusage(resource.RUSAGE_CHILDREN)
            after_self = resource.getrusage(resource.RUSAGE_SELF)
            cpu_ns = round(1e9 * sum((after_child.ru_utime - before_child.ru_utime,
                                      after_child.ru_stime - before_child.ru_stime,
                                      after_self.ru_utime - before_self.ru_utime,
                                      after_self.ru_stime - before_self.ru_stime)))
            stem = f"dev-s{seed}-{arm}"
            (HERE / f"{stem}.stdout").write_bytes(stdout)
            (HERE / f"{stem}.stderr").write_bytes(stderr)
            if arm == "rho":
                (HERE / f"{stem}.metrics.json").write_text(json.dumps(data, sort_keys=True) + "\n")
            writer.writerow((seed, position, arm, status, code, scalar, wall_ns, cpu_ns, cold,
                             base_ns, index_ns, online_ns, queries, entries,
                             hashlib.sha256(stdout).hexdigest(), hashlib.sha256(binary.read_bytes()).hexdigest()))
            sys.stdout.flush()
