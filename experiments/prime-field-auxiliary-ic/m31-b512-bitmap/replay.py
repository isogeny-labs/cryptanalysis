"""Frozen native B512 bitmap comparison with matched rho."""
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
api = runpy.run_path(str(HERE.parent / "m31-full-rust-comparison/replay.py"))
frozen = api["frozen"]
public_bytes = subprocess.check_output([
    "git", "show", "HEAD:experiments/prime-field-auxiliary-ic/m31-integrated-local-screen/fresh-public.json"], cwd=ROOT)
assert hashlib.sha256(public_bytes).hexdigest() == "dc724fc613d9c2b824b90d59c876f1f7f84b3273d8d607c648e1ba3fbc089252"
public = json.loads(public_bytes)
curve = api["Curve"](public["p"], a4=public["a"], a6=public["b"])
manifest_bytes = (HERE / "SEEDS.json").read_bytes()
manifest = json.loads(manifest_bytes)
master = bytes.fromhex(manifest["master_seed_hex"])
def derive(label):
    digest = hashlib.sha256(b"m31-b512-bitmap/v1\0" + master + b"\0" + label.encode("ascii")).digest()
    return int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)
assert manifest["walk_seeds"] == [derive(s) for s in manifest["walk_labels"]]
assert manifest["order_seed"] == derive(manifest["order_label"])
assert len(set(manifest["walk_seeds"])) == 3
blocks = [(t, s) for t in manifest["target_ids"] for s in range(3)]
random.Random(manifest["order_seed"]).shuffle(blocks)
labels = ("control", "bitmap", "rho")
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(("target", "seed", "position", "arm", "status", "exit_code", "scalar",
                 "wall_ns", "cpu_ns", "cold_ns", "base_ns", "index_ns", "online_ns",
                 "queries_or_steps", "relations", "rank", "entries", "certificate_sha256",
                 "report_sha256", "binary_sha256"))
with tempfile.TemporaryDirectory(prefix="m31-b512-bitmap-") as td:
    tmp = Path(td)
    source = tmp / "measured-source"
    source.mkdir()
    archive = subprocess.check_output(["git", "archive",
        "0012506b6", "crates/prime-field-auxiliary-ic"], cwd=ROOT)
    subprocess.run(["tar", "-xf", "-", "-C", str(source)], input=archive, check=True)
    pair_source = source / "crates/prime-field-auxiliary-ic/src/pair_index.rs"
    assert b'M31_B512_BITMAP' in pair_source.read_bytes()
    binaries = {}
    for variant in ("control", "bitmap"):
        env = os.environ.copy()
        for flag in ("M31_B512_BITMAP", "M31_HIGH_BITMAP", "M31_DUAL_BITMAP"):
            env.pop(flag, None)
        if variant == "bitmap":
            env["M31_B512_BITMAP"] = "1"
        env["CARGO_TARGET_DIR"] = str(tmp / f"target-{variant}")
        subprocess.run(["cargo", "build", "--release", "--offline", "--manifest-path",
                        str(source / "crates/prime-field-auxiliary-ic/Cargo.toml"),
                        "--bin", "m31-fast"], cwd=source, env=env, check=True)
        binaries[variant] = tmp / f"target-{variant}/release/m31-fast"
    (tmp / "common.hpp").write_bytes(frozen("comparison/common.hpp"))
    (tmp / "compare_rho.cpp").write_bytes(frozen("comparison/compare_rho.cpp"))
    rho = tmp / "compare_rho"
    subprocess.run(["c++", "-std=c++17", "-O3", "-DFIELD_BITS=31",
                    str(tmp / "compare_rho.cpp"), "-o", str(rho)], check=True)
    rho_sha = hashlib.sha256(rho.read_bytes()).hexdigest()
    for target, seed_index in blocks:
        seed = manifest["walk_seeds"][seed_index]
        qx, qy = public["targets"][target]["Q"]
        shift = (target + seed_index) % len(labels)
        identities = []
        for position, arm in enumerate(labels[shift:] + labels[:shift]):
            if arm == "rho":
                workdir = tmp / f"t{target}-s{seed_index}"
                workdir.mkdir()
                (workdir / "public.txt").write_text(
                    f'{public["p"]} {public["n"]} {public["a"]} {public["b"]}\n'
                    f'{public["G"][0]} {public["G"][1]} {qx} {qy}\n0\n')
                cmd = [str(rho), str(seed)]
                this_sha = rho_sha
            else:
                workdir = ROOT
                binary = binaries[arm]
                cmd = [str(binary), "--qx", str(qx), "--qy", str(qy), "--seed", str(seed),
                       "--columns", "512", "--summands", "2", "--method", "indexed",
                       "--base", "interval", "--lanes", "64", "--chunk", "64",
                       "--max-queries", "4000000", "--max-ms", "5000"]
                this_sha = hashlib.sha256(binary.read_bytes()).hexdigest()
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
                    certificate_sha = None
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
                    certificate_sha = hashlib.sha256(json.dumps(data.get("certificate"), sort_keys=True).encode()).hexdigest()
                    if status == "solved":
                        identities.append((scalar, data.get("work"), data.get("setup_pair_counts"),
                                                 data.get("online_pair_counts"), certificate_sha))
                if timed_out:
                    status = "timed_out"
                elif status == "solved" and not (code == 0 and scalar is not None and
                                                    curve.mul(scalar, tuple(public["G"])) == (qx, qy)):
                    status = "invalid_answer"
            except (ValueError, TypeError, KeyError, AssertionError):
                data, scalar, status = {}, None, "parse_or_verification_error"
                cold = base_ns = index_ns = online_ns = queries = relations = rank = entries = None
                certificate_sha = None
            wall_ns = perf_counter_ns() - started
            after_child = resource.getrusage(resource.RUSAGE_CHILDREN)
            after_self = resource.getrusage(resource.RUSAGE_SELF)
            cpu_ns = round(1e9 * sum((after_child.ru_utime - before_child.ru_utime,
                                      after_child.ru_stime - before_child.ru_stime,
                                      after_self.ru_utime - before_self.ru_utime,
                                      after_self.ru_stime - before_self.ru_stime)))
            stem = f"t{target}-s{seed_index}-{arm}"
            (HERE / f"{stem}.stdout").write_bytes(stdout)
            (HERE / f"{stem}.stderr").write_bytes(stderr)
            if arm == "rho":
                (HERE / f"{stem}.metrics.json").write_text(json.dumps(data, sort_keys=True) + "\n")
            writer.writerow((target, seed, position, arm, status, code, scalar, wall_ns, cpu_ns,
                             cold, base_ns, index_ns, online_ns, queries, relations, rank,
                             entries, certificate_sha, hashlib.sha256(stdout).hexdigest(), this_sha))
            sys.stdout.flush()
        if len(identities) == 2 and identities[0] != identities[1]:
            raise ValueError(f"matched B512 native collector workload changed: target {target}, seed {seed_index}")
