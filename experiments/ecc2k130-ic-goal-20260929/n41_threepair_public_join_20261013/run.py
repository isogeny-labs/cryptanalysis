#!/usr/bin/env python3
"""Frozen, capped one-process N41 public three-pair exact join."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]
SOURCE = ROOT / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
BINARY = HERE / "join3"
TARGET = (920359962848, 755404565011)
CAP_SECONDS = 300.0
CAP_RSS_BYTES = 4 * 1024**3
EXPECTED_HASHES = {
    "join3.cpp": "bfbacc6c806891fd51c6bade01243d9c09a8a5b872f2b52316d8ce0972ea4bd5",
    "join3": "103bc6546be7ef474099c749a8f8b5641be94043c1e57152b4911b8cb39d9eb2",
    "pairs.tsv": "df367421657bf29d7c47a9bd62b26c6424993e81b98d4d1f70cb7e05f0d8b22a",
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    if len(sys.argv) != 2 or not sys.argv[1].replace("_", "").isalnum():
        raise RuntimeError("usage: run.py run_label")
    run_label = sys.argv[1]
    paths = {"join3.cpp": HERE / "join3.cpp", "join3": BINARY, "pairs.tsv": SOURCE}
    hashes = {name: sha256(path) for name, path in paths.items()}
    if hashes != EXPECTED_HASHES:
        raise RuntimeError(f"frozen source hash mismatch: {hashes}")
    order = sorted(
        range(64),
        key=lambda bucket: hashlib.sha256(
            f"n41-threepair-v1|{TARGET[0]}|{TARGET[1]}|{bucket}".encode()
        ).digest(),
    )
    argv = [str(BINARY), str(SOURCE), "public", str(TARGET[0]), str(TARGET[1]),
            ",".join(map(str, order))]
    protocol = {
        "algorithm": "exact_output_first_three_pair_group_join_v1",
        "candidate_id": None,
        "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
        "public_target_xy": TARGET,
        "source_signed_states": 30952,
        "frozen_bucket_order": order,
        "source_hashes_sha256": hashes,
        "compile_command": "clang++ -O3 -std=c++17 -Wall -Wextra -Werror join3.cpp -o join3",
        "compiler": "Apple clang 17.0.0 arm64-apple-darwin25.6.0",
        "command": argv,
        "resource": {"workers": 1, "wall_cap_seconds": CAP_SECONDS,
                     "rss_cap_bytes": CAP_RSS_BYTES},
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "cpu_count_logical": os.cpu_count()},
        "status_policy": "HIT after independent replay, EXHAUSTED only after all 64 buckets, otherwise BOUNDED_UNKNOWN",
    }
    protocol_path = HERE / "public_protocol.json"
    if protocol_path.exists():
        if json.loads(protocol_path.read_text()) != json.loads(json.dumps(protocol)):
            raise RuntimeError("protocol changed")
    else:
        protocol_path.write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")
    stdout_path = HERE / f"public_{run_label}_stdout.log"
    stderr_path = HERE / f"public_{run_label}_stderr.log"
    receipt_path = HERE / f"public_{run_label}_run.json"
    if stdout_path.exists() or stderr_path.exists() or receipt_path.exists():
        raise RuntimeError("run output already exists")
    start_wall = time.time()
    start_mono = time.monotonic()
    peak_rss = 0
    stop_reason = None
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(argv, stdout=stdout, stderr=stderr, start_new_session=True)
        probe = psutil.Process(process.pid)
        try:
            while process.poll() is None:
                elapsed = time.monotonic() - start_mono
                try:
                    peak_rss = max(peak_rss, probe.memory_info().rss)
                except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                    pass
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
    status = "UNVERIFIED_HIT" if hits else ("EXHAUSTED" if exhausted else "BOUNDED_UNKNOWN")
    if exit_code != 0 and not stop_reason:
        status = "PRODUCER_FAILURE"
    receipt = {
        "status": status, "exit_code": exit_code, "stop_reason": stop_reason,
        "started_unix": start_wall, "wall_seconds": time.monotonic() - start_mono,
        "peak_observed_rss_bytes": peak_rss, "buckets_done": buckets_done,
        "hit_lines": hits, "stdout_sha256": sha256(stdout_path),
        "stderr_sha256": sha256(stderr_path), "protocol_sha256": sha256(protocol_path),
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
