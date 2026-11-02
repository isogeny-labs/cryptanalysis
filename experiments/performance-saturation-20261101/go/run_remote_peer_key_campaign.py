#!/usr/bin/env python3
"""Run the prospective four-arm A/B + byte-identical A/A Go campaign."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import l2_measure  # noqa: E402
import run_campaign as common  # noqa: E402


BASELINE = "go-baseline"
CANDIDATE = "go-candidate"
AA_LEFT = "go-baseline-aa-left"
AA_RIGHT = "go-baseline-aa-right"
ARM_ORDER = (BASELINE, CANDIDATE, AA_LEFT, AA_RIGHT)
ORDER_CYCLE = (
    (BASELINE, CANDIDATE, AA_LEFT, AA_RIGHT),
    (CANDIDATE, BASELINE, AA_RIGHT, AA_LEFT),
    (AA_LEFT, AA_RIGHT, BASELINE, CANDIDATE),
    (AA_RIGHT, AA_LEFT, CANDIDATE, BASELINE),
)
EXPECTED_ROWS = 552
ACTIVE_RESERVATION: dict[int, dict[str, object]] | None = None
ACTIVE_OUTPUT: Path | None = None
ACTIVE_EXPECTED_AFFINITY: list[int] | None = None
LOCK_PATH = "/tmp/crypto-bench.lock"


class SessionAbort(BaseException):
    pass


def _abort_on_signal(signum: int, _frame: object) -> None:
    raise SessionAbort(f"campaign received signal {signum}")


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--protocol-sha256", required=True)
    for prefix in ("baseline", "candidate", "aa-left", "aa-right"):
        parser.add_argument(f"--{prefix}-binary", type=Path, required=True)
        parser.add_argument(f"--{prefix}-sha256", required=True)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--replicates", type=int, default=20)
    parser.add_argument("--cpu", type=int, required=True)
    parser.add_argument("--reserved-cpus", required=True)
    parser.add_argument("--expected-affinity", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    return parser.parse_args()


def parse_affinity(text: str) -> list[int]:
    try:
        cpus = [int(field) for field in text.split(",")]
    except ValueError as error:
        raise ValueError(f"invalid expected affinity {text!r}") from error
    if not cpus or cpus != sorted(cpus) or len(cpus) != len(set(cpus)) or cpus[0] < 0:
        raise ValueError("expected affinity must be sorted, distinct, and nonnegative")
    return cpus


def benchmark_command(cpu: int, binary: Path, case: str) -> list[str]:
    return [
        "/usr/bin/taskset", "-c", str(cpu), str(binary), "-test.run=^$",
        f"-test.bench=^{case}$", "-test.benchmem", "-test.benchtime=100x",
        "-test.count=1", "-test.cpu=1", "-test.v", "-test.timeout=20m",
    ]


def campaign_main() -> int:
    global ACTIVE_EXPECTED_AFFINITY, ACTIVE_OUTPUT, ACTIVE_RESERVATION
    options = arguments()
    if (options.warmups, options.replicates) != (3, 20):
        raise SystemExit("frozen peer-key campaign requires warmups=3 replicates=20")
    expected_affinity = parse_affinity(options.expected_affinity)
    if sorted(os.sched_getaffinity(0)) != expected_affinity:
        raise SystemExit("session affinity differs from the frozen 32-CPU placement")
    if options.cpu == 0 or options.cpu not in expected_affinity:
        raise SystemExit("benchmark CPU must be an allowed non-housekeeping CPU")
    reserved_cpus = parse_affinity(options.reserved_cpus)
    siblings = sorted(l2_measure.smt_siblings(options.cpu))
    if (
        siblings != reserved_cpus
        or options.cpu not in reserved_cpus
        or 0 in reserved_cpus
        or not set(reserved_cpus) <= set(expected_affinity)
    ):
        raise SystemExit("reserved CPUs are not the complete non-housekeeping SMT core")
    control_affinity = [cpu for cpu in expected_affinity if cpu not in reserved_cpus]
    if not control_affinity:
        raise SystemExit("campaign needs at least one control CPU outside the measured CPU")

    arm_values = {
        BASELINE: (options.baseline_binary.resolve(), options.baseline_sha256),
        CANDIDATE: (options.candidate_binary.resolve(), options.candidate_sha256),
        AA_LEFT: (options.aa_left_binary.resolve(), options.aa_left_sha256),
        AA_RIGHT: (options.aa_right_binary.resolve(), options.aa_right_sha256),
    }
    for arm, (binary, expected) in arm_values.items():
        if not binary.is_file() or common.sha256(binary) != expected:
            raise SystemExit(f"binary identity mismatch for {arm}")
    baseline_sha = arm_values[BASELINE][1]
    if not all(arm_values[arm][1] == baseline_sha for arm in (AA_LEFT, AA_RIGHT)):
        raise SystemExit("A/A controls are not byte-identical to the A/B baseline")
    if arm_values[CANDIDATE][1] == baseline_sha:
        raise SystemExit("candidate unexpectedly equals the baseline binary")

    # The established local performance-session lock is held from before
    # preflight/reservation until after restoration and summary sealing.
    lock_stream = Path(LOCK_PATH).open("a+", encoding="utf-8")
    try:
        fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        lock_stream.close()
        raise SystemExit(f"exclusive benchmark lock is already held: {LOCK_PATH}") from error
    lock_stat = os.fstat(lock_stream.fileno())
    lock_receipt = {
        "path": LOCK_PATH,
        "exclusive": True,
        "nonblocking": True,
        "device": lock_stat.st_dev,
        "inode": lock_stat.st_ino,
        "owner_pid": os.getpid(),
    }

    options.out.mkdir(parents=True, exist_ok=False)
    ACTIVE_OUTPUT = options.out
    ACTIVE_EXPECTED_AFFINITY = expected_affinity
    output_dir = options.out / "raw/benchmark-output"
    error_dir = options.out / "raw/benchmark-stderr"
    metadata_dir = options.out / "raw/run-metadata"
    for directory in (output_dir, error_dir, metadata_dir):
        directory.mkdir(parents=True)
    os.sched_setaffinity(0, control_affinity)
    preflight = l2_measure.quiet_preflight({os.getpid()})
    moved = l2_measure.evict(set(reserved_cpus), {os.getpid()})
    ACTIVE_RESERVATION = moved
    left = l2_measure.unmovable_on(set(reserved_cpus), {os.getpid()})
    reservation = {
        "cpus": reserved_cpus,
        "smt_siblings": siblings,
        "evicted": True,
        "threads_moved": len(moved),
        "left_on_reserved": left,
    }
    taskset = shutil.which("taskset", path="/usr/bin:/bin")
    if taskset != "/usr/bin/taskset":
        raise SystemExit("frozen campaign requires /usr/bin/taskset")
    environment = {
        "PATH": "/usr/bin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
        "GOMAXPROCS": "1",
        "CGO_ENABLED": "1",
    }
    environment_sha256 = hashlib.sha256(
        json.dumps(environment, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    rows_path = options.out / "rows.jsonl"
    common.json_file(
        options.out / "manifest.json",
        {
            "schema": "go-coordinator-peer-key-campaign/2",
            "phase": options.phase,
            "protocol_sha256": options.protocol_sha256,
            "benchmark_source_sha256": common.BENCHMARK_SOURCE,
            "created": common.now(),
            "cases": list(common.CASES),
            "warmups": 3,
            "replicates": 20,
            "benchtime": "100x",
            "benchmark_cpu": options.cpu,
            "session_affinity": expected_affinity,
            "runner_affinity": control_affinity,
            "reservation": reservation,
            "environment": environment,
            "environment_sha256": environment_sha256,
            "arms": [
                {"id": arm, "binary": str(arm_values[arm][0]), "sha256": arm_values[arm][1]}
                for arm in ARM_ORDER
            ],
            "order_cycle": [list(order) for order in ORDER_CYCLE],
            "preflight": preflight,
            "l2_thresholds": l2_measure.THRESHOLDS,
            "session_lock": lock_receipt,
            "runner_sha256": common.sha256(Path(__file__).resolve()),
            "l2_measure_sha256": common.sha256(Path(l2_measure.__file__).resolve()),
            "host_start": common.host(),
        },
    )

    sequence = failures = l2_failures = 0
    for case_index, case in enumerate(common.CASES, 1):
        rounds = [(True, value) for value in range(1, 4)]
        rounds.extend((False, value) for value in range(1, 21))
        for warmup, replicate in rounds:
            ordered = ORDER_CYCLE[(replicate - 1) % len(ORDER_CYCLE)]
            for position, arm in enumerate(ordered, 1):
                sequence += 1
                kind = "warmup" if warmup else "measured"
                run_id = (
                    f"{sequence:04d}_{kind}_case{case_index:02d}_r{replicate:02d}_"
                    f"p{position}_{arm}"
                )
                stdout_path = output_dir / f"{run_id}.txt"
                stderr_path = error_dir / f"{run_id}.txt"
                metadata_path = metadata_dir / f"{run_id}.json"
                binary, digest = arm_values[arm]
                invocation = benchmark_command(options.cpu, binary, case)
                started = common.now()
                instrumentation_error = None
                try:
                    execution = l2_measure.run_measured(
                        invocation,
                        {options.cpu},
                        environment,
                        stdout_path,
                        stderr_path,
                        options.timeout_seconds,
                        set(reserved_cpus),
                    )
                    parsed = common.parse_output(stdout_path.read_bytes())
                    l2 = l2_measure.evaluate_l2(execution, preflight, reservation)
                except Exception as error:  # seal this attempt, then continue the frozen schedule
                    instrumentation_error = {
                        "type": type(error).__name__,
                        "message": str(error),
                    }
                    if not stdout_path.exists():
                        stdout_path.write_bytes(b"")
                    if not stderr_path.exists():
                        stderr_path.write_bytes(b"")
                    with stderr_path.open("ab") as stream:
                        stream.write(
                            (
                                "\npreregistered instrumentation error: "
                                f"{type(error).__name__}: {error}\n"
                            ).encode("utf-8", errors="replace")
                        )
                        stream.flush()
                        os.fsync(stream.fileno())
                    parsed = common.parse_output(stdout_path.read_bytes())
                    execution = {
                        "instrumentation_error": instrumentation_error,
                        "pinned_cpus": [options.cpu],
                        "reserved_cpus": reserved_cpus,
                        "child_affinity_observed": None,
                        "tree_affinity": {"tasks_outside": None, "cpus_seen": [], "examples": []},
                        "subreaper": None,
                        "descendants_killed": None,
                        "exit": {"returncode": None, "signal": None, "timed_out": False},
                        "wall_ns": 0,
                        "rusage": {
                            "user_s": 0.0, "sys_s": 0.0, "maxrss_kib": 0,
                            "minflt": 0, "majflt": 0, "nvcsw": 0, "nivcsw": 0,
                        },
                        "schedstat": {
                            "run_ns": 0, "wait_ns": 0, "slices": 0,
                            "threads_seen": 0,
                            "sample_interval_seconds": l2_measure.SAMPLE_INTERVAL_SECONDS,
                        },
                        "max_threads_observed": 0,
                        "contention": {
                            "samples": 0,
                            "samples_with_foreign_runnable": 0,
                            "foreign_examples": [],
                            "pinned_cpu_jiffies_delta": {},
                            "psi_total_delta_us": {"cpu": None, "memory": None},
                            "procs_running_after": None,
                        },
                    }
                    l2 = {
                        "required_level": "L2",
                        "earned_level": "L0",
                        "passes": False,
                        "blocking": ["instrumentation_error"],
                        "checks": [],
                        "thresholds": dict(l2_measure.THRESHOLDS),
                    }
                expected_fingerprints = (
                    {"vector_sha256"}
                    if case.startswith("BenchmarkStateVersionVector/")
                    else {"lines_sha256", "reached_vector_sha256"}
                )
                complete = (
                    instrumentation_error is None
                    and execution["exit"]["returncode"] == 0
                    and not execution["exit"]["timed_out"]
                    and execution["descendants_killed"] == 0
                    and parsed["iterations"] == 100
                    and {"ns/op", "cpu-ns/op", "B/op", "allocs/op"}.issubset(parsed["metrics"])
                    and expected_fingerprints == set(parsed["fingerprints"])
                )
                failures += int(not complete)
                l2_failures += int(not l2["passes"])
                usage = execution["rusage"]
                row = {
                    "schema": "go-coordinator-peer-key-row/2",
                    "run_id": run_id,
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
                    "outer_wall_ns": execution["wall_ns"],
                    "exit_status": execution["exit"]["returncode"],
                    "timed_out": execution["exit"]["timed_out"],
                    "instrumentation_error": instrumentation_error,
                    "command": invocation,
                    "environment": environment,
                    "environment_sha256": environment_sha256,
                    "session_affinity": expected_affinity,
                    "runner_affinity": control_affinity,
                    "reservation_cpus": reserved_cpus,
                    "expected_child_affinity": [options.cpu],
                    "parsed": parsed,
                    "rusage": {
                        "user_seconds": usage["user_s"],
                        "system_seconds": usage["sys_s"],
                        "max_rss_kib": usage["maxrss_kib"],
                        "minor_faults": usage["minflt"],
                        "major_faults": usage["majflt"],
                        "voluntary_context_switches": usage["nvcsw"],
                        "involuntary_context_switches": usage["nivcsw"],
                    },
                    "execution": execution,
                    "isolation": l2,
                    "artifacts": {
                        "stdout": str(stdout_path.relative_to(options.out)),
                        "stdout_sha256": common.sha256(stdout_path),
                        "stderr": str(stderr_path.relative_to(options.out)),
                        "stderr_sha256": common.sha256(stderr_path),
                        "metadata": str(metadata_path.relative_to(options.out)),
                    },
                }
                common.json_file(metadata_path, row)
                common.append_row(rows_path, row)
                print(
                    f"{sequence:04d}/{EXPECTED_ROWS} {kind} {case} r={replicate:02d} "
                    f"p={position} arm={arm} status={row['status']} l2={l2['passes']}",
                    flush=True,
                )

    restore_receipt = l2_measure.restore(ACTIVE_RESERVATION or {})
    ACTIVE_RESERVATION = None
    os.sched_setaffinity(0, expected_affinity)
    runner_affinity_after_restore = sorted(os.sched_getaffinity(0))
    restore_receipt["runner_affinity_after_restore"] = runner_affinity_after_restore
    restore_receipt["runner_affinity_passes"] = runner_affinity_after_restore == expected_affinity
    restore_receipt["passes"] = bool(
        restore_receipt["passes"] and restore_receipt["runner_affinity_passes"]
    )
    common.json_file(
        options.out / "summary.json",
        {
            "schema": "go-coordinator-peer-key-campaign-summary/2",
            "phase": options.phase,
            "protocol_sha256": options.protocol_sha256,
            "finished": common.now(),
            "planned": EXPECTED_ROWS,
            "attempted": sequence,
            "failures": failures,
            "l2_failures": l2_failures,
            "rows_sha256": common.sha256(rows_path),
            "benchmark_cpu": options.cpu,
            "session_affinity": expected_affinity,
            "runner_affinity": control_affinity,
            "reservation": reservation,
            "restoration": restore_receipt,
            "session_lock": lock_receipt,
            "environment": environment,
            "environment_sha256": environment_sha256,
            "preflight": preflight,
            "order_cycle": [list(order) for order in ORDER_CYCLE],
            "host_end": common.host(),
        },
    )
    fcntl.flock(lock_stream.fileno(), fcntl.LOCK_UN)
    lock_stream.close()
    ACTIVE_OUTPUT = None
    ACTIVE_EXPECTED_AFFINITY = None
    # Isolation failures invalidate only clocks. Counted allocation and exact
    # correctness remain analyzable when every benchmark attempt completed.
    return int(failures != 0)


def main() -> int:
    global ACTIVE_EXPECTED_AFFINITY, ACTIVE_OUTPUT, ACTIVE_RESERVATION
    previous_term = signal.signal(signal.SIGTERM, _abort_on_signal)
    try:
        return campaign_main()
    finally:
        if ACTIVE_RESERVATION is not None:
            emergency = l2_measure.restore(ACTIVE_RESERVATION)
            if ACTIVE_EXPECTED_AFFINITY is not None:
                try:
                    os.sched_setaffinity(0, ACTIVE_EXPECTED_AFFINITY)
                    emergency["runner_affinity_after_restore"] = sorted(os.sched_getaffinity(0))
                    emergency["runner_affinity_passes"] = (
                        emergency["runner_affinity_after_restore"] == ACTIVE_EXPECTED_AFFINITY
                    )
                except OSError as error:
                    emergency["runner_affinity_error"] = error.errno
                    emergency["runner_affinity_passes"] = False
                emergency["passes"] = bool(
                    emergency.get("passes") and emergency["runner_affinity_passes"]
                )
            if ACTIVE_OUTPUT is not None and ACTIVE_OUTPUT.is_dir():
                common.json_file(ACTIVE_OUTPUT / "emergency-restoration.json", emergency)
            ACTIVE_RESERVATION = None
        signal.signal(signal.SIGTERM, previous_term)


if __name__ == "__main__":
    sys.exit(main())
