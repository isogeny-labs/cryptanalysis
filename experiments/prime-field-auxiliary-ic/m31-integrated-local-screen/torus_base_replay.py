"""Cold same-target interval, torus, random and rho comparison on public M31 points."""
import argparse
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
public = json.loads((HERE / "fresh-public.json").read_text())
curve = api["Curve"](public["p"], a4=public["a"], a6=public["b"])
binary = Path("/Volumes/SSD990/m31-bitmap-tuned-target/release/m31-fast")
assert hashlib.sha256(binary.read_bytes()).hexdigest() == "e5f13b960f620e6aaae3c99ca17ee82963b4df981d89585688b8bbe9a35b4804"

parser = argparse.ArgumentParser()
parser.add_argument("--pilot", action="store_true")
args = parser.parse_args()
blocks = [(0, 0)] if args.pilot else [(t, s) for t in range(5) for s in range(3)]
if not args.pilot:
    random.Random(2026112748).shuffle(blocks)
labels = ("interval", "torus", "random") if args.pilot else ("interval", "torus", "random", "rho")
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(("target", "seed", "position", "arm", "status", "exit_code", "scalar",
                 "wall_ns", "cpu_ns", "cold_ns", "base_ns", "index_ns", "online_ns",
                 "torus_depth", "basis_sha256", "pair_entries", "queries", "relations",
                 "rank", "stdout_sha256"))
with tempfile.TemporaryDirectory(prefix="m31-torus-rho-") as td:
    tmp = Path(td)
    rho = tmp / "compare_rho"
    if not args.pilot:
        (tmp / "common.hpp").write_bytes(frozen("comparison/common.hpp"))
        (tmp / "compare_rho.cpp").write_bytes(frozen("comparison/compare_rho.cpp"))
        subprocess.run(["c++", "-std=c++17", "-O3", "-DFIELD_BITS=31",
                        str(tmp / "compare_rho.cpp"), "-o", str(rho)], check=True)
    for target, seed in blocks:
        qx, qy = public["targets"][target]["Q"]
        order = labels[(target + seed) % len(labels):] + labels[:(target + seed) % len(labels)]
        for position, arm in enumerate(order):
            if arm == "rho":
                run_dir = tmp / f"t{target}-s{seed}"
                run_dir.mkdir()
                (run_dir / "public.txt").write_text(
                    f'{public["p"]} {public["n"]} {public["a"]} {public["b"]}\n'
                    f'{public["G"][0]} {public["G"][1]} {qx} {qy}\n0\n')
                cmd = [str(rho), str(seed)]
            else:
                run_dir = ROOT
                cmd = [str(binary), "--qx", str(qx), "--qy", str(qy), "--seed", str(seed),
                       "--columns", "384", "--summands", "2", "--method", "indexed",
                       "--base", arm, "--base-seed", "1", "--lanes", "64",
                       "--max-queries", "4000000", "--max-ms", "5000"]
            before_child = resource.getrusage(resource.RUSAGE_CHILDREN)
            before_self = resource.getrusage(resource.RUSAGE_SELF)
            started = perf_counter_ns()
            try:
                process = subprocess.run(cmd, cwd=run_dir, capture_output=True, timeout=20)
                stdout, stderr, code = process.stdout, process.stderr, process.returncode
                timed_out = False
            except subprocess.TimeoutExpired as exc:
                stdout, stderr, code = exc.stdout or b"", exc.stderr or b"", None
                timed_out = True
            data = json.loads(stdout) if stdout and arm != "rho" else {}
            if arm == "rho":
                metrics = run_dir / "metrics.json"
                data = json.loads(metrics.read_text()) if metrics.exists() else {}
                scalar = data.get("recovered")
                status = "timed_out" if timed_out else ("solved" if code == 0 and scalar is not None else "error")
                cold = base_ns = index_ns = online_ns = torus_depth = basis_sha = entries = relations = rank = None
                queries = data.get("walk_steps")
            else:
                scalar = data.get("scalar")
                status = "timed_out" if timed_out else data.get("status", "error")
                cold, base_ns, index_ns, online_ns = (data.get(k) for k in
                    ("cold_to_report_ns", "base_construction_ns", "pair_index_ns", "online_ns"))
                torus_depth = data.get("torus_subset_depth")
                basis_sha = hashlib.sha256(json.dumps(data.get("base_points"), separators=(",", ":")).encode()).hexdigest() if data.get("base_points") else None
                work = data.get("work") or {}
                entries = (data.get("setup_pair_counts") or {}).get("entries")
                queries, relations, rank = (work.get(k) for k in ("queries", "relations", "matrix_rank"))
            if status == "solved":
                assert code == 0 and scalar is not None
                assert curve.mul(scalar, tuple(public["G"])) == (qx, qy)
            elif status == "timed_out":
                assert code is None
            else:
                assert code != 0
            wall = perf_counter_ns() - started
            after_child = resource.getrusage(resource.RUSAGE_CHILDREN)
            after_self = resource.getrusage(resource.RUSAGE_SELF)
            cpu = round(1e9 * sum((after_child.ru_utime - before_child.ru_utime,
                                  after_child.ru_stime - before_child.ru_stime,
                                  after_self.ru_utime - before_self.ru_utime,
                                  after_self.ru_stime - before_self.ru_stime)))
            stem = f'torus-{"pilot-" if args.pilot else ""}t{target}-s{seed}-{arm}'
            (HERE / f"{stem}.stdout").write_bytes(stdout)
            (HERE / f"{stem}.stderr").write_bytes(stderr)
            if arm == "rho":
                (HERE / f"{stem}.metrics.json").write_text(json.dumps(data, sort_keys=True) + "\n")
            writer.writerow((target, seed, position, arm, status, code, scalar, wall, cpu,
                             cold, base_ns, index_ns, online_ns, torus_depth, basis_sha,
                             entries, queries, relations, rank, hashlib.sha256(stdout).hexdigest()))
            sys.stdout.flush()
