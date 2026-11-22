#!/usr/bin/env python3
"""Finish the exact N41 three-pair source after two capped prefixes."""
import json
import os
from pathlib import Path
import subprocess
import time

import psutil

from run_fast import BINARY, CAP_RSS_BYTES, EXPECTED_HASHES, HERE, SOURCE, sha


def main():
    for name, path in {"join3_fast.cpp": HERE / "join3_fast.cpp",
                       "join3_fast": BINARY, "pairs.tsv": SOURCE}.items():
        if sha(path) != EXPECTED_HASHES[name]:
            raise RuntimeError(f"hash mismatch: {name}")
    parent = json.loads((HERE / "public_protocol.json").read_text())
    baseline = json.loads((HERE / "public_retry1_run.json").read_text())
    fast = json.loads((HERE / "fast_run.json").read_text())
    completed = baseline["buckets_done"] + fast["buckets_done"]
    order = parent["frozen_bucket_order"]
    if baseline["status"] != "BOUNDED_UNKNOWN" or fast["status"] != "BOUNDED_UNKNOWN":
        raise RuntimeError("unexpected prior status")
    if completed != order[:len(completed)]:
        raise RuntimeError("prior buckets do not form exact frozen prefix")
    remaining = order[len(completed):]
    if not remaining:
        raise RuntimeError("no remaining buckets")
    target = parent["public_target_xy"]
    argv = [str(BINARY), str(SOURCE), "public", str(target[0]), str(target[1]),
            ",".join(map(str, remaining))]
    cap_seconds = 300.0
    protocol = {
        "algorithm": "exact_output_first_three_pair_group_join_pmull_v1",
        "candidate_id": None, "command": argv,
        "parent_protocol_sha256": sha(HERE / "public_protocol.json"),
        "baseline_run_sha256": sha(HERE / "public_retry1_run.json"),
        "fast_run_sha256": sha(HERE / "fast_run.json"),
        "completed_buckets": completed, "remaining_bucket_order": remaining,
        "source_hashes_sha256": EXPECTED_HASHES,
        "resource": {"workers": 1, "wall_cap_seconds": cap_seconds,
                     "rss_cap_bytes": CAP_RSS_BYTES},
    }
    protocol_path = HERE / "tail_protocol.json"
    stdout_path = HERE / "tail_stdout.log"
    stderr_path = HERE / "tail_stderr.log"
    receipt_path = HERE / "tail_run.json"
    if any(path.exists() for path in (protocol_path, stdout_path, stderr_path, receipt_path)):
        raise RuntimeError("tail output already exists")
    protocol_path.write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")
    start = time.monotonic()
    peak_rss = 0
    stop_reason = None
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(argv, stdout=stdout, stderr=stderr, start_new_session=True)
        probe = psutil.Process(process.pid)
        try:
            while process.poll() is None:
                try:
                    peak_rss = max(peak_rss, probe.memory_info().rss)
                except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                    pass
                if time.monotonic() - start >= cap_seconds:
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
    buckets_done = [int(line.split()[1]) for line in lines if line.startswith("BUCKET_DONE ")]
    hits = [line for line in lines if line.startswith("HIT ")]
    exhausted = any(line.startswith("EXHAUSTED ") for line in lines)
    status = "UNVERIFIED_HIT" if hits else ("SOURCE_EXHAUSTED" if exhausted else "BOUNDED_UNKNOWN")
    if exit_code != 0 and not stop_reason:
        status = "PRODUCER_FAILURE"
    receipt = {
        "status": status, "exit_code": exit_code, "stop_reason": stop_reason,
        "wall_seconds": time.monotonic() - start, "peak_observed_rss_bytes": peak_rss,
        "buckets_done": buckets_done, "hit_lines": hits,
        "stdout_sha256": sha(stdout_path), "stderr_sha256": sha(stderr_path),
        "protocol_sha256": sha(protocol_path),
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
