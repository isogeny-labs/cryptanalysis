#!/usr/bin/env python3
"""Capped continuation over the buckets completed by neither baseline run."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time

import psutil

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SOURCE = GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
BINARY = HERE / "join3_fast"
CAP_SECONDS = 600.0
CAP_RSS_BYTES = 4 * 1024**3
EXPECTED_HASHES = {
    "join3_fast.cpp": "33d2260fcf074d7dda1ad9997d389ab682f682de52091239bf819f2cbbbfa63c",
    "join3_fast": "3f3681f6dd3d27fdf7421d6f7bbdef6cf3da6aee938beddd236dd6dfe4b8b187",
    "pairs.tsv": "df367421657bf29d7c47a9bd62b26c6424993e81b98d4d1f70cb7e05f0d8b22a",
}


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    paths = {"join3_fast.cpp": HERE / "join3_fast.cpp", "join3_fast": BINARY,
             "pairs.tsv": SOURCE}
    hashes = {name: sha(path) for name, path in paths.items()}
    if hashes != EXPECTED_HASHES:
        raise RuntimeError(f"hash mismatch: {hashes}")
    parent = json.loads((HERE / "public_protocol.json").read_text())
    previous = json.loads((HERE / "public_retry1_run.json").read_text())
    completed = previous["buckets_done"]
    if previous["status"] != "BOUNDED_UNKNOWN" or completed != parent["frozen_bucket_order"][:4]:
        raise RuntimeError("unexpected completed bucket set")
    target = parent["public_target_xy"]
    remaining = parent["frozen_bucket_order"][4:]
    argv = [str(BINARY), str(SOURCE), "public", str(target[0]), str(target[1]),
            ",".join(map(str, remaining))]
    protocol = {
        "algorithm": "exact_output_first_three_pair_group_join_pmull_v1",
        "candidate_id": None,
        "parent_protocol_sha256": sha(HERE / "public_protocol.json"),
        "previous_run_sha256": sha(HERE / "public_retry1_run.json"),
        "already_completed_buckets": completed,
        "remaining_bucket_order": remaining,
        "public_target_xy": target,
        "source_hashes_sha256": hashes,
        "compile_command": "clang++ -O3 -std=c++17 -march=armv8-a+crypto -Wall -Wextra -Werror join3_fast.cpp -o join3_fast",
        "compiler": "Apple clang 17.0.0 arm64-apple-darwin25.6.0",
        "command": argv,
        "resource": {"workers": 1, "wall_cap_seconds": CAP_SECONDS,
                     "rss_cap_bytes": CAP_RSS_BYTES},
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "cpu_count_logical": os.cpu_count()},
        "field_selftest": "100000 deterministic differential products against slow_mul before join",
    }
    protocol_path = HERE / "fast_protocol.json"
    if protocol_path.exists() or (HERE / "fast_stdout.log").exists() or (HERE / "fast_run.json").exists():
        raise RuntimeError("fast output already exists")
    protocol_path.write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")
    start_wall = time.time()
    start_mono = time.monotonic()
    peak_rss = 0
    stop_reason = None
    stdout_path = HERE / "fast_stdout.log"
    stderr_path = HERE / "fast_stderr.log"
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(argv, stdout=stdout, stderr=stderr, start_new_session=True)
        probe = psutil.Process(process.pid)
        try:
            while process.poll() is None:
                try:
                    peak_rss = max(peak_rss, probe.memory_info().rss)
                except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                    pass
                elapsed = time.monotonic() - start_mono
                if elapsed >= CAP_SECONDS:
                    stop_reason = "wall_cap"
                elif peak_rss >= CAP_RSS_BYTES:
                    stop_reason = "rss_cap"
                if stop_reason:
                    os.killpg(process.pid, 9)
                    break
                time.sleep(0.1)
        finally:
            if process.poll() is None:
                os.killpg(process.pid, 9)
            exit_code = process.wait()
    lines = stdout_path.read_text().splitlines()
    hits = [line for line in lines if line.startswith("HIT ")]
    buckets_done = [int(line.split()[1]) for line in lines if line.startswith("BUCKET_DONE ")]
    exhausted = any(line.startswith("EXHAUSTED ") for line in lines)
    status = "UNVERIFIED_HIT" if hits else ("SOURCE_EXHAUSTED" if exhausted else "BOUNDED_UNKNOWN")
    if exit_code != 0 and not stop_reason:
        status = "PRODUCER_FAILURE"
    receipt = {
        "status": status, "exit_code": exit_code, "stop_reason": stop_reason,
        "started_unix": start_wall, "wall_seconds": time.monotonic() - start_mono,
        "peak_observed_rss_bytes": peak_rss, "buckets_done": buckets_done,
        "hit_lines": hits, "stdout_sha256": sha(stdout_path),
        "stderr_sha256": sha(stderr_path), "protocol_sha256": sha(protocol_path),
    }
    (HERE / "fast_run.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
