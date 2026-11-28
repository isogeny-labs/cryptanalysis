"""Frozen cold B384/B512/rho comparison on the five public M31 targets."""
import csv
import hashlib
import json
import random
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
frozen = api["frozen"]
public_bytes = subprocess.check_output([
    "git", "show", "HEAD:experiments/prime-field-auxiliary-ic/m31-integrated-local-screen/fresh-public.json"], cwd=ROOT)
assert hashlib.sha256(public_bytes).hexdigest() == "dc724fc613d9c2b824b90d59c876f1f7f84b3273d8d607c648e1ba3fbc089252"
public = json.loads(public_bytes)
curve = api["Curve"](public["p"], a4=public["a"], a6=public["b"])
binary = Path("/Volumes/SSD990/m31-bitmap-tuned-target/release/m31-fast")
binary_sha = hashlib.sha256(binary.read_bytes()).hexdigest()
assert binary_sha == "e5f13b960f620e6aaae3c99ca17ee82963b4df981d89585688b8bbe9a35b4804"
blocks = [(t, s) for t in range(5) for s in range(3)]
random.Random(2026112852).shuffle(blocks)
labels = ("b384", "b512", "rho")
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(("target", "seed", "position", "arm", "status", "exit_code", "scalar",
                 "wall_ns", "cpu_ns", "cold_ns", "base_ns", "index_ns", "online_ns",
                 "queries_or_steps", "relations", "rank", "entries", "report_sha256", "binary_sha256"))
with tempfile.TemporaryDirectory(prefix="m31-b512-cold-") as td:
    tmp = Path(td)
    (tmp / "common.hpp").write_bytes(frozen("comparison/common.hpp"))
    (tmp / "compare_rho.cpp").write_bytes(frozen("comparison/compare_rho.cpp"))
    rho = tmp / "compare_rho"
    subprocess.run(["c++", "-std=c++17", "-O3", "-DFIELD_BITS=31",
                    str(tmp / "compare_rho.cpp"), "-o", str(rho)], check=True)
    rho_sha = hashlib.sha256(rho.read_bytes()).hexdigest()
    for target, seed in blocks:
        qx, qy = public["targets"][target]["Q"]
        shift = (target + seed) % len(labels)
        for position, arm in enumerate(labels[shift:] + labels[:shift]):
            if arm == "rho":
                workdir = tmp / f"t{target}-s{seed}"
                workdir.mkdir()
                (workdir / "public.txt").write_text(
                    f'{public["p"]} {public["n"]} {public["a"]} {public["b"]}\n'
                    f'{public["G"][0]} {public["G"][1]} {qx} {qy}\n0\n')
                cmd = [str(rho), str(seed)]
                this_sha = rho_sha
            else:
                workdir = ROOT
                size = int(arm[1:])
                cmd = [str(binary), "--qx", str(qx), "--qy", str(qy), "--seed", str(seed),
                       "--columns", str(size), "--summands", "2", "--method", "indexed",
                       "--base", "interval", "--lanes", "64", "--chunk", "64",
                       "--max-queries", "4000000", "--max-ms", "5000"]
                this_sha = binary_sha
            before_child = resource.getrusage(resource.RUSAGE_CHILDREN)
            before_self = resource.getrusage(resource.RUSAGE_SELF)
            started = perf_counter_ns()
            try:
                process = subprocess.run(cmd, cwd=workdir, capture_output=True, timeout=20)
                stdout, stderr, code = process.stdout, process.stderr, process.returncode
                timed_out = False
            except subprocess.TimeoutExpired as exc:
                stdout, stderr, code = exc.stdout or b"", exc.stderr or b"", None
                timed_out = True
            try:
                if arm == "rho":
                    metrics = workdir / "metrics.json"
                    data = json.loads(metrics.read_text()) if metrics.exists() else {}
                    scalar = data.get("recovered")
                    cold = base_ns = index_ns = online_ns = entries = relations = rank = None
                    queries = data.get("walk_steps")
                    status = "solved" if code == 0 and scalar is not None else "error"
                else:
                    data = json.loads(stdout) if stdout else {}
                    scalar = data.get("scalar")
                    status = data.get("status", "error")
                    cold = data.get("cold_to_report_ns")
                    base_ns = data.get("base_construction_ns")
                    index_ns = data.get("pair_index_ns")
                    online_ns = data.get("online_ns")
                    work = data.get("work") or {}
                    queries = work.get("queries")
                    relations = work.get("relations")
                    rank = work.get("matrix_rank")
                    entries = (data.get("setup_pair_counts") or {}).get("entries")
                if timed_out:
                    status = "timed_out"
                elif status == "solved" and not (code == 0 and scalar is not None and
                                                    curve.mul(scalar, tuple(public["G"])) == (qx, qy)):
                    status = "invalid_answer"
            except (ValueError, TypeError, KeyError, AssertionError):
                data, scalar, status = {}, None, "parse_or_verification_error"
                cold = base_ns = index_ns = online_ns = queries = relations = rank = entries = None
            wall_ns = perf_counter_ns() - started
            after_child = resource.getrusage(resource.RUSAGE_CHILDREN)
            after_self = resource.getrusage(resource.RUSAGE_SELF)
            cpu_ns = round(1e9 * sum((after_child.ru_utime - before_child.ru_utime,
                                      after_child.ru_stime - before_child.ru_stime,
                                      after_self.ru_utime - before_self.ru_utime,
                                      after_self.ru_stime - before_self.ru_stime)))
            stem = f"t{target}-s{seed}-{arm}"
            (HERE / f"{stem}.stdout").write_bytes(stdout)
            (HERE / f"{stem}.stderr").write_bytes(stderr)
            if arm == "rho":
                (HERE / f"{stem}.metrics.json").write_text(json.dumps(data, sort_keys=True) + "\n")
            writer.writerow((target, seed, position, arm, status, code, scalar, wall_ns, cpu_ns,
                             cold, base_ns, index_ns, online_ns, queries, relations, rank,
                             entries, hashlib.sha256(stdout).hexdigest(), this_sha))
            sys.stdout.flush()
