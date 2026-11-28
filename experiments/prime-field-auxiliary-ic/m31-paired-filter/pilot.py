"""Recorded cold pilot on one frozen public target, with full answer replay."""
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
api = runpy.run_path(str(HERE.parent / "m31-full-rust-comparison/replay.py"))
curve = api["Curve"](2147483647, a4=2, a6=14)
g, q = (1, 814455902), (1767503692, 244402461)
bins = {
    "control": (Path("/Volumes/SSD990/m31-bitmap-tuned-target/release/m31-fast"),
                "e5f13b960f620e6aaae3c99ca17ee82963b4df981d89585688b8bbe9a35b4804"),
    "paired": (Path("/Volumes/SSD990/m31-paired-filter-target/release/m31-fast"),
               "818d956f5bd27509d6c8753519889122c5d70cd3bf04d6f98b41e00cccb17ffd"),
}
for binary, expected in bins.values():
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == expected
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(("block", "position", "arm", "status", "exit_code", "wall_ns", "cpu_ns",
                 "cold_ns", "index_ns", "online_ns", "queries", "relations", "rank",
                 "lookups", "generated_candidates", "scalar", "certificate_sha256",
                 "report_sha256", "binary_sha256"))
for block in range(3):
    order = ("control", "paired", "paired", "control") if block % 2 == 0 else (
        "paired", "control", "control", "paired")
    for position, arm in enumerate(order):
        binary, binary_sha = bins[arm]
        cmd = [str(binary), "--qx", str(q[0]), "--qy", str(q[1]), "--seed", "0",
               "--columns", "384", "--summands", "3", "--method", "indexed",
               "--base", "interval", "--lanes", "64", "--chunk", "64",
               "--max-queries", "4000000", "--max-ms", "5000"]
        before_child = resource.getrusage(resource.RUSAGE_CHILDREN)
        before_self = resource.getrusage(resource.RUSAGE_SELF)
        started = perf_counter_ns()
        try:
            process = subprocess.run(cmd, cwd=ROOT, capture_output=True, timeout=20)
            stdout, stderr, code = process.stdout, process.stderr, process.returncode
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            stdout, stderr, code = exc.stdout or b"", exc.stderr or b"", None
            timed_out = True
        try:
            report = json.loads(stdout)
            scalar = report.get("scalar")
            status = report.get("status", "error")
            if timed_out:
                status = "timed_out"
            elif status == "solved" and not (code == 0 and scalar is not None and
                                                curve.mul(scalar, g) == q):
                status = "invalid_answer"
            certificate_sha = hashlib.sha256(json.dumps(
                report.get("certificate"), sort_keys=True).encode()).hexdigest()
            work = report.get("work") or {}
            pair = report.get("online_pair_counts") or {}
            cold, index, online = (report.get(k) for k in (
                "cold_to_report_ns", "pair_index_ns", "online_ns"))
            queries, relations, rank = (work.get(k) for k in (
                "queries", "relations", "matrix_rank"))
            lookups, candidates = pair.get("lookups"), pair.get("generated_candidates")
        except (ValueError, TypeError, KeyError, AssertionError):
            status, scalar, certificate_sha = "parse_or_verification_error", None, None
            cold = index = online = queries = relations = rank = lookups = candidates = None
        wall_ns = perf_counter_ns() - started
        after_child = resource.getrusage(resource.RUSAGE_CHILDREN)
        after_self = resource.getrusage(resource.RUSAGE_SELF)
        cpu_ns = round(1e9 * sum((after_child.ru_utime - before_child.ru_utime,
                                  after_child.ru_stime - before_child.ru_stime,
                                  after_self.ru_utime - before_self.ru_utime,
                                  after_self.ru_stime - before_self.ru_stime)))
        stem = f"block{block}-pos{position}-{arm}"
        (HERE / f"{stem}.stdout").write_bytes(stdout)
        (HERE / f"{stem}.stderr").write_bytes(stderr)
        writer.writerow((block, position, arm, status, code, wall_ns, cpu_ns,
                         cold, index, online, queries, relations, rank, lookups, candidates,
                         scalar, certificate_sha, hashlib.sha256(stdout).hexdigest(), binary_sha))
        sys.stdout.flush()
