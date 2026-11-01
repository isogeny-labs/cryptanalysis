#!/usr/bin/env python3
"""Execute the remote mirrored Go A/B schedule on one observed allowed CPU."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_campaign as common  # noqa: E402


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--left-arm", required=True)
    parser.add_argument("--left-binary", type=Path, required=True)
    parser.add_argument("--left-sha256", required=True)
    parser.add_argument("--right-arm", required=True)
    parser.add_argument("--right-binary", type=Path, required=True)
    parser.add_argument("--right-sha256", required=True)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--replicates", type=int, default=20)
    parser.add_argument("--cpu", type=int, required=True)
    parser.add_argument("--expected-affinity", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    return parser.parse_args()


def parse_affinity(text: str) -> list[int]:
    try:
        cpus = [int(field) for field in text.split(",")]
    except ValueError as error:
        raise ValueError(f"invalid expected affinity {text!r}") from error
    if not cpus or cpus != sorted(cpus) or len(cpus) != len(set(cpus)) or cpus[0] < 0:
        raise ValueError(f"expected affinity must be sorted distinct nonnegative CPUs: {text!r}")
    return cpus


def require_affinity(expected: list[int], observed: list[int] | None = None) -> None:
    current = sorted(os.sched_getaffinity(0)) if observed is None else sorted(observed)
    if current != expected:
        raise RuntimeError(f"allowed CPU affinity changed: observed={current}, expected={expected}")


def benchmark_command(cpu: int, binary: Path, case: str) -> list[str]:
    return [
        "taskset", "-c", str(cpu), str(binary),
        "-test.run=^$", f"-test.bench=^{case}$", "-test.benchmem",
        "-test.benchtime=100x", "-test.count=1", "-test.cpu=1",
        "-test.v", "-test.timeout=20m",
    ]


def main() -> int:
    options = arguments()
    if (options.warmups, options.replicates) != (3, 20):
        raise SystemExit("frozen remote campaign requires warmups=3 replicates=20")
    expected_affinity = parse_affinity(options.expected_affinity)
    if options.cpu not in expected_affinity:
        raise SystemExit(f"benchmark CPU {options.cpu} is outside {expected_affinity}")
    require_affinity(expected_affinity)
    arms = (
        (options.left_arm, options.left_binary.resolve(), options.left_sha256),
        (options.right_arm, options.right_binary.resolve(), options.right_sha256),
    )
    for arm, binary, expected in arms:
        if not binary.is_file() or common.sha256(binary) != expected:
            raise SystemExit(f"binary identity mismatch for {arm}: {binary}")

    options.out.mkdir(parents=True, exist_ok=False)
    output_dir = options.out / "raw/benchmark-output"
    error_dir = options.out / "raw/benchmark-stderr"
    metadata_dir = options.out / "raw/run-metadata"
    for directory in (output_dir, error_dir, metadata_dir):
        directory.mkdir(parents=True)
    rows = options.out / "rows.jsonl"
    common.json_file(
        options.out / "manifest.json",
        {
            "schema": "go-coordinator-campaign/1",
            "phase": options.phase,
            "protocol_sha256": options.protocol_sha256,
            "benchmark_source_sha256": common.BENCHMARK_SOURCE,
            "created": common.now(),
            "cases": list(common.CASES),
            "warmups": 3,
            "replicates": 20,
            "benchtime": "100x",
            "benchmark_cpu": options.cpu,
            "expected_affinity": expected_affinity,
            "arms": [
                {"id": arm, "binary": str(binary), "sha256": digest}
                for arm, binary, digest in arms
            ],
            "runner_sha256": common.sha256(Path(__file__).resolve()),
            "host_start": common.host(),
        },
    )

    environment = os.environ.copy()
    environment.update({"GOMAXPROCS": "1", "CGO_ENABLED": "1"})
    sequence = 0
    failures = 0
    for case_index, case in enumerate(common.CASES, 1):
        rounds = [(True, r) for r in range(1, 4)] + [(False, r) for r in range(1, 21)]
        for warmup, replicate in rounds:
            ordered = arms if replicate % 2 else tuple(reversed(arms))
            for position, (arm, binary, digest) in enumerate(ordered, 1):
                require_affinity(expected_affinity)
                sequence += 1
                kind = "warmup" if warmup else "measured"
                stem = (
                    f"{sequence:04d}_{kind}_case{case_index:02d}_r{replicate:02d}_"
                    f"p{position}_{arm}"
                )
                stdout_path = output_dir / f"{stem}.txt"
                stderr_path = error_dir / f"{stem}.txt"
                metadata_path = metadata_dir / f"{stem}.json"
                invocation = benchmark_command(options.cpu, binary, case)
                started = common.now()
                before_host = common.host()
                before_usage = common.usage()
                before_ns = time.monotonic_ns()
                timed_out = False
                process = subprocess.Popen(
                    invocation, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    env=environment, start_new_session=True,
                )
                try:
                    stdout, stderr = process.communicate(timeout=options.timeout_seconds)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    os.killpg(process.pid, signal.SIGKILL)
                    stdout, stderr = process.communicate()
                elapsed = time.monotonic_ns() - before_ns
                after_usage = common.usage()
                after_host = common.host()
                require_affinity(expected_affinity, after_host["self_affinity"])
                stdout_path.write_bytes(stdout)
                stderr_path.write_bytes(stderr)
                parsed = common.parse_output(stdout)
                fingerprints = (
                    {"vector_sha256"} if case.startswith("BenchmarkStateVersionVector/")
                    else {"lines_sha256", "reached_vector_sha256"}
                )
                complete = (
                    process.returncode == 0 and not timed_out and parsed["iterations"] == 100
                    and {"ns/op", "cpu-ns/op", "B/op", "allocs/op"}.issubset(parsed["metrics"])
                    and fingerprints.issubset(parsed["fingerprints"])
                )
                failures += int(not complete)
                row = {
                    "schema": "go-coordinator-row/1",
                    "run_id": stem,
                    "phase": options.phase,
                    "protocol_sha256": options.protocol_sha256,
                    "benchmark_source_sha256": common.BENCHMARK_SOURCE,
                    "arm": arm,
                    "binary": str(binary),
                    "binary_sha256": digest,
                    "case": case,
                    "case_index": case_index,
                    "replicate": replicate,
                    "warmup": warmup,
                    "order_position": position,
                    "sequence": sequence,
                    "status": "completed" if complete else "not_completed",
                    "outcome_class": "verified" if complete else "instrument_error",
                    "started": started,
                    "finished": common.now(),
                    "outer_wall_ns": elapsed,
                    "exit_status": process.returncode,
                    "timed_out": timed_out,
                    "command": invocation,
                    "environment": {"GOMAXPROCS": "1", "CGO_ENABLED": "1"},
                    "expected_affinity": expected_affinity,
                    "parsed": parsed,
                    "rusage": common.usage_delta(before_usage, after_usage),
                    "host_before": before_host,
                    "host_after": after_host,
                    "artifacts": {
                        "stdout": str(stdout_path.relative_to(options.out)),
                        "stdout_sha256": common.sha256(stdout_path),
                        "stderr": str(stderr_path.relative_to(options.out)),
                        "stderr_sha256": common.sha256(stderr_path),
                        "metadata": str(metadata_path.relative_to(options.out)),
                    },
                }
                common.json_file(metadata_path, row)
                common.append_row(rows, row)
                print(
                    f"{sequence:04d}/0276 {kind} {case} r={replicate:02d} "
                    f"p={position} arm={arm} status={row['status']}", flush=True,
                )

    require_affinity(expected_affinity)
    common.json_file(
        options.out / "summary.json",
        {
            "schema": "go-coordinator-campaign-summary/1",
            "phase": options.phase,
            "protocol_sha256": options.protocol_sha256,
            "finished": common.now(),
            "planned": 276,
            "attempted": sequence,
            "failures": failures,
            "rows_sha256": common.sha256(rows),
            "benchmark_cpu": options.cpu,
            "expected_affinity": expected_affinity,
            "host_end": common.host(),
        },
    )
    return int(failures != 0)


if __name__ == "__main__":
    sys.exit(main())
