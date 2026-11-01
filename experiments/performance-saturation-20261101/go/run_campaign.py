#!/usr/bin/env python3
"""Execute one frozen mirrored two-arm Go coordinator campaign."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import time


CASES = (
    "BenchmarkStateVersionVector/log_1024",
    "BenchmarkStateVersionVector/log_8192",
    "BenchmarkStateDeltaSinceCaughtUp/log_1024",
    "BenchmarkStateDeltaSinceCaughtUp/log_8192",
    "BenchmarkStateDeltaSinceOneBehind/log_1024",
    "BenchmarkStateDeltaSinceOneBehind/log_8192",
)
BASELINE_AA_PROTOCOL = "8120278e7c96fd2f6bc5a2ffa4a02f3e02f4668c492f3882a2b6a1d170adf696"
BENCHMARK_SOURCE = "b13eafcc112ada81b104c3fde3ad51a75cb80e9a051f9644a66fc27d30218dbd"


def arguments() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--phase", required=True)
    p.add_argument("--protocol-sha256", default=BASELINE_AA_PROTOCOL)
    p.add_argument("--left-arm", required=True)
    p.add_argument("--left-binary", type=Path, required=True)
    p.add_argument("--left-sha256", required=True)
    p.add_argument("--right-arm", required=True)
    p.add_argument("--right-binary", type=Path, required=True)
    p.add_argument("--right-sha256", required=True)
    p.add_argument("--warmups", type=int, default=3)
    p.add_argument("--replicates", type=int, default=20)
    p.add_argument("--cpu", type=int, default=0)
    p.add_argument("--timeout-seconds", type=int, default=1800)
    return p.parse_args()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def read(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def host() -> dict[str, object]:
    info: dict[str, str] = {}
    first = (read("/proc/cpuinfo") or "").split("\n\n", 1)[0]
    for line in first.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            info[key.strip()] = value.strip()
    stat = (read("/proc/stat") or "").splitlines()
    fields = stat[0].split()[1:] if stat and stat[0].startswith("cpu ") else []
    return {
        "timestamp": now(),
        "cpu_model": info.get("model name"),
        "microcode": info.get("microcode"),
        "cpu_mhz": info.get("cpu MHz"),
        "kernel": os.uname().release,
        "machine": os.uname().machine,
        "steal_ticks": int(fields[7]) if len(fields) > 7 else None,
        "psi_cpu": read("/proc/pressure/cpu"),
        "psi_memory": read("/proc/pressure/memory"),
        "governor_cpu0": read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"),
        "frequency_khz_cpu0": read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"),
        "temperature_millicelsius": read("/sys/class/thermal/thermal_zone0/temp"),
        "self_affinity": sorted(os.sched_getaffinity(0)),
    }


def usage() -> resource.struct_rusage:
    return resource.getrusage(resource.RUSAGE_CHILDREN)


def usage_delta(a: resource.struct_rusage, b: resource.struct_rusage) -> dict[str, float | int]:
    return {
        "user_seconds": b.ru_utime - a.ru_utime,
        "system_seconds": b.ru_stime - a.ru_stime,
        "max_rss_kib": b.ru_maxrss,
        "minor_faults": b.ru_minflt - a.ru_minflt,
        "major_faults": b.ru_majflt - a.ru_majflt,
        "voluntary_context_switches": b.ru_nvcsw - a.ru_nvcsw,
        "involuntary_context_switches": b.ru_nivcsw - a.ru_nivcsw,
    }


def number(text: str) -> int | float | str:
    try:
        return int(text) if re.fullmatch(r"[-+]?[0-9]+", text) else float(text)
    except ValueError:
        return text


def parse_output(raw: bytes) -> dict[str, object]:
    text = raw.decode("utf-8", errors="replace")
    line = None
    for candidate in text.splitlines():
        if candidate.startswith("Benchmark") and "ns/op" in candidate:
            line = candidate
    metrics: dict[str, object] = {}
    name = None
    iterations = None
    if line:
        fields = line.split()
        name = fields[0]
        iterations = number(fields[1])
        for i in range(2, len(fields) - 1, 2):
            metrics[fields[i + 1]] = number(fields[i])
    fingerprints: dict[str, str] = {}
    for key in ("vector_sha256", "lines_sha256", "reached_vector_sha256"):
        found = re.findall(rf"\b{key}=([0-9a-f]{{64}})\b", text)
        if found:
            fingerprints[key] = found[-1]
    return {
        "benchmark_line": line,
        "benchmark_name": name,
        "iterations": iterations,
        "metrics": metrics,
        "fingerprints": fingerprints,
    }


def json_file(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_row(path: Path, value: object) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
        f.flush()
        os.fsync(f.fileno())


def main() -> int:
    args = arguments()
    if (args.warmups, args.replicates, args.cpu) != (3, 20, 0):
        raise SystemExit("frozen campaign requires warmups=3 replicates=20 cpu=0")
    arms = (
        (args.left_arm, args.left_binary.resolve(), args.left_sha256),
        (args.right_arm, args.right_binary.resolve(), args.right_sha256),
    )
    for arm, binary, expected in arms:
        if not binary.is_file() or sha256(binary) != expected:
            raise SystemExit(f"binary identity mismatch for {arm}: {binary}")

    args.out.mkdir(parents=True, exist_ok=False)
    output_dir = args.out / "raw" / "benchmark-output"
    error_dir = args.out / "raw" / "benchmark-stderr"
    metadata_dir = args.out / "raw" / "run-metadata"
    for directory in (output_dir, error_dir, metadata_dir):
        directory.mkdir(parents=True)
    rows = args.out / "rows.jsonl"
    json_file(
        args.out / "manifest.json",
        {
            "schema": "go-coordinator-campaign/1",
            "phase": args.phase,
            "protocol_sha256": args.protocol_sha256,
            "benchmark_source_sha256": BENCHMARK_SOURCE,
            "created": now(),
            "cases": list(CASES),
            "warmups": 3,
            "replicates": 20,
            "benchtime": "100x",
            "cpu": 0,
            "arms": [
                {"id": arm, "binary": str(binary), "sha256": digest}
                for arm, binary, digest in arms
            ],
            "runner_sha256": sha256(Path(__file__).resolve()),
            "host_start": host(),
        },
    )

    env = os.environ.copy()
    env.update({"GOMAXPROCS": "1", "CGO_ENABLED": "1"})
    sequence = 0
    failures = 0
    for case_index, case in enumerate(CASES, 1):
        rounds = [(True, r) for r in range(1, 4)] + [(False, r) for r in range(1, 21)]
        for warmup, replicate in rounds:
            ordered = arms if replicate % 2 else tuple(reversed(arms))
            for position, (arm, binary, digest) in enumerate(ordered, 1):
                sequence += 1
                kind = "warmup" if warmup else "measured"
                stem = f"{sequence:04d}_{kind}_case{case_index:02d}_r{replicate:02d}_p{position}_{arm}"
                stdout_path = output_dir / f"{stem}.txt"
                stderr_path = error_dir / f"{stem}.txt"
                metadata_path = metadata_dir / f"{stem}.json"
                command = [
                    "taskset", "-c", "0", str(binary),
                    "-test.run=^$", f"-test.bench=^{case}$", "-test.benchmem",
                    "-test.benchtime=100x", "-test.count=1", "-test.cpu=1",
                    "-test.v", "-test.timeout=20m",
                ]
                started = now()
                before_host = host()
                before_usage = usage()
                before_ns = time.monotonic_ns()
                timed_out = False
                proc = subprocess.Popen(
                    command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    env=env, start_new_session=True,
                )
                try:
                    stdout, stderr = proc.communicate(timeout=args.timeout_seconds)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    os.killpg(proc.pid, signal.SIGKILL)
                    stdout, stderr = proc.communicate()
                elapsed = time.monotonic_ns() - before_ns
                after_usage = usage()
                after_host = host()
                stdout_path.write_bytes(stdout)
                stderr_path.write_bytes(stderr)
                parsed = parse_output(stdout)
                fingerprints = (
                    {"vector_sha256"} if case.startswith("BenchmarkStateVersionVector/")
                    else {"lines_sha256", "reached_vector_sha256"}
                )
                complete = (
                    proc.returncode == 0 and not timed_out and parsed["iterations"] == 100
                    and {"ns/op", "cpu-ns/op", "B/op", "allocs/op"}.issubset(parsed["metrics"])
                    and fingerprints.issubset(parsed["fingerprints"])
                )
                failures += int(not complete)
                row = {
                    "schema": "go-coordinator-row/1",
                    "run_id": stem,
                    "phase": args.phase,
                    "protocol_sha256": args.protocol_sha256,
                    "benchmark_source_sha256": BENCHMARK_SOURCE,
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
                    "finished": now(),
                    "outer_wall_ns": elapsed,
                    "exit_status": proc.returncode,
                    "timed_out": timed_out,
                    "command": command,
                    "environment": {"GOMAXPROCS": "1", "CGO_ENABLED": "1"},
                    "parsed": parsed,
                    "rusage": usage_delta(before_usage, after_usage),
                    "host_before": before_host,
                    "host_after": after_host,
                    "artifacts": {
                        "stdout": str(stdout_path.relative_to(args.out)),
                        "stdout_sha256": sha256(stdout_path),
                        "stderr": str(stderr_path.relative_to(args.out)),
                        "stderr_sha256": sha256(stderr_path),
                        "metadata": str(metadata_path.relative_to(args.out)),
                    },
                }
                json_file(metadata_path, row)
                append_row(rows, row)
                print(
                    f"{sequence:04d}/0276 {kind} {case} r={replicate:02d} "
                    f"p={position} arm={arm} status={row['status']}", flush=True,
                )

    json_file(
        args.out / "summary.json",
        {
            "schema": "go-coordinator-campaign-summary/1",
            "phase": args.phase,
            "protocol_sha256": args.protocol_sha256,
            "finished": now(),
            "planned": 276,
            "attempted": sequence,
            "failures": failures,
            "rows_sha256": sha256(rows),
            "host_end": host(),
        },
    )
    return int(failures != 0)


if __name__ == "__main__":
    sys.exit(main())
