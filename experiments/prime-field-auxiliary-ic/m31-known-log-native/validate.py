"""Frozen five-target same-host known-log, IC, rho and BSGS panel."""
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
known = Path("/Volumes/SSD990/m31-known-log-target/release/m31-known-log-control")
ic = Path("/Volumes/SSD990/m31-bitmap-tuned-target/release/m31-fast")
assert hashlib.sha256(known.read_bytes()).hexdigest() == "5bbb1cab0ed20e55baca1e54ad6668d5a77298c7b92121efbd16290f27f4f570"
assert hashlib.sha256(ic.read_bytes()).hexdigest() == "e5f13b960f620e6aaae3c99ca17ee82963b4df981d89585688b8bbe9a35b4804"
blocks = [(t, s) for t in range(5) for s in range(3)]
random.Random(2026112751).shuffle(blocks)
labels = ("known256", "ic384", "rho", "bsgs")
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(("target", "seed", "position", "arm", "status", "exit_code", "scalar",
                 "wall_ns", "cpu_ns", "cold_ns", "base_ns", "index_ns", "online_ns",
                 "queries_or_steps", "entries", "report_sha256", "binary_sha256"))
with tempfile.TemporaryDirectory(prefix="m31-known-validation-") as td:
    tmp = Path(td)
    (tmp / "common.hpp").write_bytes(frozen("comparison/common.hpp"))
    (tmp / "compare_rho.cpp").write_bytes(frozen("comparison/compare_rho.cpp"))
    rho = tmp / "compare_rho"
    subprocess.run(["c++", "-std=c++17", "-O3", "-DFIELD_BITS=31",
                    str(tmp / "compare_rho.cpp"), "-o", str(rho)], check=True)
    bsgs_source = subprocess.check_output([
        "git", "show", "HEAD:experiments/chained-transfer-public-target/norm-point-reuse-01/ct322_prime31_bsgs.rs"], cwd=ROOT)
    (HERE / "ct322-source.sha256").write_text(hashlib.sha256(bsgs_source).hexdigest() + "\n")
    (tmp / "ct322_prime31_bsgs.rs").write_bytes(bsgs_source)
    bsgs = tmp / "bsgs"
    subprocess.run(["rustc", "--edition=2021", "-C", "opt-level=3", "-C", "debuginfo=0",
                    str(tmp / "ct322_prime31_bsgs.rs"), "-o", str(bsgs)], check=True)
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
                binary, cmd = rho, [str(rho), str(seed)]
            elif arm == "bsgs":
                workdir = ROOT
                binary = bsgs
                cmd = [str(bsgs), *(str(x) for x in (
                    public["p"], public["a"], public["b"], public["n"],
                    *public["G"], qx, qy))]
            elif arm == "ic384":
                workdir = ROOT
                binary = ic
                cmd = [str(ic), "--qx", str(qx), "--qy", str(qy), "--seed", str(seed),
                       "--columns", "384", "--summands", "2", "--method", "indexed",
                       "--base", "interval", "--lanes", "64", "--max-queries", "4000000",
                       "--max-ms", "5000"]
            else:
                workdir = ROOT
                binary = known
                cmd = [str(known), "--qx", str(qx), "--qy", str(qy), "--seed", str(seed),
                       "--columns", "256"]
            before_child = resource.getrusage(resource.RUSAGE_CHILDREN)
            before_self = resource.getrusage(resource.RUSAGE_SELF)
            started = perf_counter_ns()
            try:
                result = subprocess.run(cmd, cwd=workdir, capture_output=True, timeout=20)
                stdout, stderr, code = result.stdout, result.stderr, result.returncode
                timed_out = False
            except subprocess.TimeoutExpired as exc:
                stdout, stderr, code, timed_out = exc.stdout or b"", exc.stderr or b"", None, True
            data = json.loads(stdout) if stdout and arm != "rho" else {}
            if arm == "rho":
                metrics = workdir / "metrics.json"
                data = json.loads(metrics.read_text()) if metrics.exists() else {}
                scalar = data.get("recovered")
                status = "timed_out" if timed_out else ("solved" if code == 0 and scalar is not None else "error")
                cold = base_ns = index_ns = online_ns = entries = None
                queries = data.get("walk_steps")
            else:
                scalar = data.get("scalar", data.get("result_scalar"))
                status = "timed_out" if timed_out else data.get("status", "solved" if code == 0 and scalar is not None else "error")
                cold = data.get("cold_to_report_ns", data.get("inside_ns"))
                base_ns = data.get("base_ns", data.get("base_construction_ns"))
                index_ns = data.get("index_ns", data.get("pair_index_ns"))
                online_ns = data.get("online_ns")
                entries = data.get("entries", data.get("baby_table_entries", (data.get("setup_pair_counts") or {}).get("entries")))
                queries = data.get("queries", data.get("giant_iterations", (data.get("work") or {}).get("queries")))
            if status == "solved":
                assert code == 0 and scalar is not None and curve.mul(scalar, tuple(public["G"])) == (qx, qy)
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
            stem = f"val-t{target}-s{seed}-{arm}"
            (HERE / f"{stem}.stdout").write_bytes(stdout)
            (HERE / f"{stem}.stderr").write_bytes(stderr)
            if arm == "rho":
                (HERE / f"{stem}.metrics.json").write_text(json.dumps(data, sort_keys=True) + "\n")
            writer.writerow((target, seed, position, arm, status, code, scalar, wall_ns, cpu_ns,
                             cold, base_ns, index_ns, online_ns, queries, entries,
                             hashlib.sha256(stdout).hexdigest(), hashlib.sha256(binary.read_bytes()).hexdigest()))
            sys.stdout.flush()
