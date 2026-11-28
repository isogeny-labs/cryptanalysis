"""Frozen public M31 size-limited bitmap versus exact lookup and rho."""
import csv
import hashlib
import json
import os
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
helpers = runpy.run_path(str(HERE.parent / "m31-full-rust-comparison/replay.py"))
frozen = helpers["frozen"]
public_bytes = (HERE / "fresh-public.json").read_bytes()
assert hashlib.sha256(public_bytes).hexdigest() == "dc724fc613d9c2b824b90d59c876f1f7f84b3273d8d607c648e1ba3fbc089252"
public = json.loads(public_bytes)
curve = helpers["Curve"](public["p"], a4=public["a"], a6=public["b"])
assert len(public["targets"]) == 5
workers = {
    "control": Path("/Volumes/SSD990/m31-bitmap-control-target/release/m31-fast"),
    "tuned": Path("/Volumes/SSD990/m31-bitmap-tuned-target/release/m31-fast"),
}
worker_sha = {
    "control": "7301092fd58bb502e14daef709595114467374312c306d8ebf6a57de0127f494",
    "tuned": "e5f13b960f620e6aaae3c99ca17ee82963b4df981d89585688b8bbe9a35b4804",
}
for label, path in workers.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == worker_sha[label]

labels = ("control384", "tuned384", "control768", "tuned768", "rho")
blocks = [(target["index"], seed) for target in public["targets"] for seed in range(3)]
random.Random(2026112746).shuffle(blocks)
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(["target", "seed", "position", "configuration", "status", "exit_code",
                 "scalar", "wall_ns", "cpu_ns", "cold_ns", "index_ns", "online_ns",
                 "queries_or_steps", "relations", "entries", "report_sha256"])
with tempfile.TemporaryDirectory(prefix="m31-bitmap-rho-", dir=os.environ.get("M31_REPLAY_TMPDIR")) as td:
    tmp = Path(td)
    (tmp / "common.hpp").write_bytes(frozen("comparison/common.hpp"))
    (tmp / "compare_rho.cpp").write_bytes(frozen("comparison/compare_rho.cpp"))
    rho = tmp / "compare_rho"
    subprocess.run(["c++", "-std=c++17", "-O3", "-DFIELD_BITS=31",
                    str(tmp / "compare_rho.cpp"), "-o", str(rho)], check=True)
    for target_index, seed in blocks:
        target = public["targets"][target_index]
        qx, qy = target["Q"]
        shift = (target_index + seed) % len(labels)
        order = labels[shift:] + labels[:shift]
        matched = {}
        for position, label in enumerate(order):
            if label == "rho":
                run_dir = tmp / f"t{target_index}-s{seed}"
                run_dir.mkdir()
                (run_dir / "public.txt").write_text(
                    f'{public["p"]} {public["n"]} {public["a"]} {public["b"]}\n'
                    f'{public["G"][0]} {public["G"][1]} {qx} {qy}\n0\n')
                cmd = [str(rho), str(seed)]
            else:
                run_dir = ROOT
                columns = int(label[-3:])
                binary = workers["tuned" if label.startswith("tuned") else "control"]
                cmd = [str(binary), "--qx", str(qx), "--qy", str(qy), "--seed", str(seed),
                       "--columns", str(columns), "--summands", "2", "--method", "indexed",
                       "--base", "interval", "--lanes", "64", "--max-queries", "4000000",
                       "--max-ms", "5000"]
            before_child = resource.getrusage(resource.RUSAGE_CHILDREN)
            before_self = resource.getrusage(resource.RUSAGE_SELF)
            started = perf_counter_ns()
            try:
                process = subprocess.run(cmd, cwd=run_dir, capture_output=True, timeout=20)
                stdout, stderr, exit_code = process.stdout, process.stderr, process.returncode
                timed_out = False
            except subprocess.TimeoutExpired as error:
                stdout, stderr, exit_code = error.stdout or b"", error.stderr or b"", None
                timed_out = True
            stem = f"bitmap-t{target_index}-s{seed}-{label}"
            if label == "rho":
                metrics = run_dir / "metrics.json"
                data = json.loads(metrics.read_text()) if metrics.exists() else {}
                scalar = data.get("recovered")
                status = "timed_out" if timed_out else ("solved" if exit_code == 0 and scalar is not None else "error")
                cold_ns = index_ns = online_ns = relations = entries = None
                queries = data.get("walk_steps")
                digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
            else:
                data = json.loads(stdout) if stdout else {}
                scalar = data.get("scalar")
                status = "timed_out" if timed_out else data.get("status", "error")
                cold_ns = data.get("cold_to_report_ns")
                index_ns = data.get("pair_index_ns")
                online_ns = data.get("online_ns")
                work = data.get("work") or {}
                setup = data.get("setup_pair_counts") or {}
                queries = work.get("queries")
                relations = work.get("relations")
                entries = setup.get("entries")
                digest = hashlib.sha256(stdout).hexdigest()
                key = label[-3:]
                identity = (status, scalar, work, setup, data.get("online_pair_counts"),
                            data.get("certificate"))
                if key in matched:
                    assert identity == matched[key], (target_index, seed, key)
                matched[key] = identity
            if status == "solved":
                assert exit_code == 0 and scalar is not None
                assert curve.mul(scalar, tuple(public["G"])) == (qx, qy)
            elif timed_out:
                assert exit_code is None
            else:
                assert exit_code != 0
            wall_ns = perf_counter_ns() - started
            after_child = resource.getrusage(resource.RUSAGE_CHILDREN)
            after_self = resource.getrusage(resource.RUSAGE_SELF)
            cpu_ns = round(1e9 * (after_child.ru_utime - before_child.ru_utime
                                 + after_child.ru_stime - before_child.ru_stime
                                 + after_self.ru_utime - before_self.ru_utime
                                 + after_self.ru_stime - before_self.ru_stime))
            (HERE / f"{stem}.stdout").open("xb").write(stdout)
            (HERE / f"{stem}.stderr").open("xb").write(stderr)
            if label == "rho":
                (HERE / f"{stem}.metrics.json").open("x").write(json.dumps(data, sort_keys=True) + "\n")
            writer.writerow([target_index, seed, position, label, status, exit_code, scalar,
                             wall_ns, cpu_ns, cold_ns, index_ns, online_ns, queries,
                             relations, entries, digest])
            sys.stdout.flush()
