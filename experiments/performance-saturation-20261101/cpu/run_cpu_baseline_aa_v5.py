#!/usr/bin/env python3
"""One-shot orchestration for the prospective CPU baseline A/A v5 study.

``plan`` is side-effect free unless ``--out`` is supplied.  ``run`` refuses an
existing v5 result root and never resumes or retries it.  The low-level
``callgrind-one`` command is invoked only by the frozen plan, once per arm and
cell, so a failed Callgrind child cannot suppress later diagnostic attempts.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
from typing import Any


REPO = Path("/workspace/cryptanalysis")
HERE = REPO / "experiments/performance-saturation-20261101/cpu"
RUN_ROOT = Path("/workspace/.benchmarks/performance-saturation/cpu/baseline-aa-v5")
V4_ROOT = Path("/workspace/.benchmarks/performance-saturation/cpu/baseline-aa-v4")
V4_PROTOCOL = HERE / "protocol-baseline-aa-exact-v4.json"
GLOBAL_LOCK = Path("/workspace/.benchmarks/performance-saturation/local/global-cpu.lock")
PYTHON = Path("/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3.12")
PROTOCOL_TOOL = Path("/workspace/crypto-autoresearcher/tools/experiment_protocol.py")
PROTOCOL_SCHEMA = Path("/workspace/crypto-autoresearcher/schemas/experiment-protocol.v1.json")
EXPORT_SCHEMA = Path("/workspace/crypto-autoresearcher/schemas/experiment-export.v1.json")
ISOLATED = Path("/workspace/crypto/target/release/isolated_bench")
PERFINDEX = REPO / "scripts/perf/perfindex.py"
VALGRIND = Path("/workspace/.tools/valgrind/bin/valgrind")
PERF = Path("/workspace/.tools/perf/usr/bin/perf")
PERF_LIB = "/workspace/.tools/perf/usr/lib/x86_64-linux-gnu"
RUST_BINARY = V4_ROOT / "build/base-rust/perfbench"
C_BINARY = V4_ROOT / "build/base-c/ca_perfbench"
ANALYZER = HERE / "analyze_cpu_baseline_aa_v5.py"
RUNNER = Path(__file__).resolve()
ATTEMPT_TIMEOUT_SECONDS = 86_400

RUST_IDS = (
    "gf2_la/rref_random_4940x8357",
    "gf2_la/rref_macaulay_k5m3d5",
    "gf2_la/echelon_macaulay_k5m3d5",
    "bool_gb/matrix_f5_deg4_m2_n23",
    "bool_gb/solve_matrixf5_m2_n17",
    "field_ec/f2m_mul_sqr_m131_64k",
    "field_ec/f2m_mul_sqr_m163_64k",
    "field_ec/f2m_mul_sqr_m233_64k",
    "field_ec/f2m_inv_m163_2k",
    "field_ec/binary_scalar_mul_sect163k1_x8",
)
C_IDS = (
    "field_ec/c_mont_mul_x8", "field_ec/c_zp_op_chain", "field_ec/c_powmod",
    "field_ec/c_mont_pow", "field_ec/c_invmod", "field_ec/c_sqrtmod",
    "field_ec/c_is_prime", "field_ec/c_factorize", "field_ec/c_ec_add_chain",
    "field_ec/c_ec_batch_add", "field_ec/c_ec_scalar_mul",
    "field_ec/c_ec_count_points", "dlp/c_rho_ec36", "dlp/c_rho_ec44",
    "dlp/c_rho_ec44_mt", "dlp/c_rho_zp40", "dlp/c_kangaroo_ec56_w34",
    "dlp/c_kangaroo_zp61_w36", "dlp/c_bsgs_ec32", "dlp/c_bsgs_zp36",
    "dlp/c_grumpy_ec32", "dlp/c_pohlig_ec48s", "dlp/c_pohlig_zp61s",
    "dlp/c_precomp_build_ec32", "dlp/c_precomp_online_ec32",
    "dlp/c_glv_rho_j0_32", "dlp/c_gpu_rho_emulate_ec32", "dlp/c_cheon56",
    "relation/c_ic_precompute_zp44", "relation/c_ic_precompute_zp52",
    "relation/c_ic_randexp_zp36", "relation/c_ic_log_zp44",
    "relation/c_linsolve_sparse", "relation/c_dense_solve",
)
ALL_IDS = tuple(sorted((*RUST_IDS, *C_IDS)))
FIXED_RECORD_IDS = (
    "gf2_la/rref_random_4940x8357",
    "bool_gb/matrix_f5_deg4_m2_n23",
    "field_ec/f2m_mul_sqr_m163_64k",
)


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest_value(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_id(kernel: str) -> str:
    return kernel.replace("/", "_")


def binary_for(kernel: str) -> Path:
    return RUST_BINARY if kernel in RUST_IDS else C_BINARY


def reserve_prefix(isolation: Path, label: str) -> list[str]:
    return [
        str(ISOLATED), "reserve", "--lock", str(GLOBAL_LOCK), "--wait",
        "--cpus", "0-3", "--settle", "2", "--max-other-cpu", "0.10",
        "--max-psi", "5", "--period", "5", "--out", str(isolation),
        "--label", label, "--",
    ]


def wall_commands() -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    sessions = (
        ("rust-1t", RUST_BINARY, RUST_IDS, 1, "0"),
        ("c-1t", C_BINARY, C_IDS, 1, "0"),
        ("rust-4t", RUST_BINARY, RUST_IDS, 4, "0-3"),
        ("c-4t", C_BINARY, C_IDS, 4, "0-3"),
    )
    for session, binary, ids, threads, taskset in sessions:
        language = "rust" if session.startswith("rust") else "c"
        panel = "1t" if threads == 1 else "4t"
        output = RUN_ROOT / f"wall-{panel}/{language}/compare"
        isolation = RUN_ROOT / f"wall-{panel}/{language}/isolation.jsonl"
        argv = reserve_prefix(isolation, f"cpu-baseline-aa-v5-{session}")
        argv += [
            "env", "PYTHONHASHSEED=0", f"RAYON_NUM_THREADS={threads}",
            f"OMP_NUM_THREADS={threads}", "OPENBLAS_NUM_THREADS=1",
            str(PYTHON), str(PERFINDEX), "compare", "--base", str(binary),
            "--cand", str(binary), "--out", str(output),
        ]
        if language == "rust":
            for kernel in ids:
                argv += ["--exact-filter", kernel]
        else:
            argv.append("--full")
        argv += [
            "--rounds", "6", "--threads", str(threads), "--samples", "5",
            "--max-seconds", "2.0", "--timeout", "1800", "--taskset",
            taskset, "--no-aa", "--seed", "20260926",
        ]
        commands.append({"id": session, "argv": argv, "timeout_seconds": ATTEMPT_TIMEOUT_SECONDS})
    return commands


def callgrind_commands() -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    ordinal = 0
    for kernel in ALL_IDS:
        for arm in ("A", "B"):
            ordinal += 1
            stem = f"{ordinal:03d}_{arm}_{safe_id(kernel)}"
            isolation = RUN_ROOT / f"profiles/callgrind/{stem}.isolation.jsonl"
            output = RUN_ROOT / f"profiles/callgrind/{stem}"
            argv = reserve_prefix(isolation, f"cpu-baseline-aa-v5-callgrind-{ordinal:03d}-{arm}")
            argv += [
                "taskset", "-c", "0", "env",
                "PATH=/workspace/.tools/valgrind/bin:/usr/bin:/bin",
                "PYTHONHASHSEED=0", "RAYON_NUM_THREADS=1", "OMP_NUM_THREADS=1",
                "OPENBLAS_NUM_THREADS=1", str(PYTHON), str(RUNNER),
                "callgrind-one", "--binary", str(binary_for(kernel)),
                "--kernel", kernel, "--out", str(output),
            ]
            commands.append({
                "ordinal": ordinal, "arm": arm, "kernel": kernel,
                "output": str(output), "argv": argv,
                "timeout_seconds": ATTEMPT_TIMEOUT_SECONDS,
            })
    return commands


def perf_stat_commands() -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    ordinal = 0
    for kernel in ALL_IDS:
        for arm in ("A", "B"):
            ordinal += 1
            stem = f"{ordinal:03d}_{arm}_{safe_id(kernel)}"
            output = RUN_ROOT / f"profiles/perf-stat/{stem}.csv"
            isolation = RUN_ROOT / f"profiles/perf-stat/{stem}.isolation.jsonl"
            argv = reserve_prefix(isolation, f"cpu-baseline-aa-v5-perf-stat-{ordinal:03d}-{arm}")
            argv += [
                "env", f"LD_LIBRARY_PATH={PERF_LIB}", "taskset", "-c", "0",
                str(PERF), "stat", "-x,", "--no-big-num", "-o", str(output),
                "-e", "task-clock,cpu-clock,context-switches,page-faults", "--",
                str(binary_for(kernel)), "run", "--filter", kernel, "--exact",
                "--samples", "5", "--min-samples", "5", "--max-seconds", "2.0",
            ]
            commands.append({
                "ordinal": ordinal, "arm": arm, "kernel": kernel,
                "output": str(output), "argv": argv,
                "timeout_seconds": ATTEMPT_TIMEOUT_SECONDS,
            })
    return commands


def perf_record_command(ordinal: int, kernel: str) -> dict[str, Any]:
    stem = f"{ordinal:03d}_A_{safe_id(kernel)}"
    output = RUN_ROOT / f"profiles/perf-record/{stem}.data"
    isolation = RUN_ROOT / f"profiles/perf-record/{stem}.isolation.jsonl"
    argv = reserve_prefix(isolation, f"cpu-baseline-aa-v5-perf-record-{ordinal:03d}")
    argv += [
        "env", f"LD_LIBRARY_PATH={PERF_LIB}", "taskset", "-c", "0", str(PERF),
        "record", "-e", "cpu-clock", "-F", "99", "-g", "--call-graph", "dwarf",
        "-o", str(output), "--", str(binary_for(kernel)), "run", "--filter",
        kernel, "--exact", "--samples", "5", "--min-samples", "5",
        "--max-seconds", "2.0",
    ]
    return {
        "ordinal": ordinal, "arm": "A", "kernel": kernel,
        "output": str(output), "argv": argv,
        "timeout_seconds": ATTEMPT_TIMEOUT_SECONDS,
    }


def perf_record_candidate_templates() -> list[dict[str, Any]]:
    """Bind every command the data-derived slots are allowed to select."""
    return [
        perf_record_command(ordinal, kernel)
        for ordinal in range(4, 9)
        for kernel in sorted(C_IDS)
    ]


def callgrind_inner_argv(binary: Path, kernel: str) -> list[str]:
    """The exact argv used by perfindex.instr_one at the frozen source."""
    return [
        "valgrind", "--tool=callgrind", "--callgrind-out-file=/dev/null",
        "--instr-atstart=no", str(binary), "run", "--filter", kernel,
        "--exact", "--instr",
    ]


def build_plan() -> dict[str, Any]:
    wall = wall_commands()
    callgrind = callgrind_commands()
    perf_stat = perf_stat_commands()
    fixed_record = [perf_record_command(i, kid) for i, kid in enumerate(FIXED_RECORD_IDS, 1)]
    derived_record = perf_record_candidate_templates()
    plan = {
        "schema": "cpu-baseline-aa-v5-command-plan/v1",
        "run_root": str(RUN_ROOT),
        "retained_artifact_root": str(V4_ROOT),
        "wall": wall,
        "callgrind": callgrind,
        "perf_stat": perf_stat,
        "perf_record": {
            "fixed": fixed_record,
            "derived_slots": [4, 5, 6, 7, 8],
            "selection": "all 34 C baseline-A Callgrind Ir values required; descending Ir, then ascending kernel id",
            "derived_candidates": derived_record,
        },
        "digests": {
            "wall": digest_value(wall),
            "callgrind": digest_value(callgrind),
            "perf_stat": digest_value(perf_stat),
            "perf_record_fixed": digest_value(fixed_record),
            "perf_record_derived_candidates": digest_value(derived_record),
        },
        "counts": {"wall_sessions": 4, "callgrind_attempts": 88, "perf_stat_attempts": 88, "perf_record_attempts": 8},
    }
    # A plan cannot contain its own whole-document hash.  This binds the
    # canonical preimage before the single self-describing digest is added;
    # start.json separately binds the exact persisted command-plan file.
    plan["digests"]["plan_preimage"] = digest_value(plan)
    return plan


def write_json_once(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def write_text_once(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(value)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def signal_process_group(proc: subprocess.Popen[str], sig: signal.Signals) -> None:
    try:
        os.killpg(proc.pid, sig)
    except ProcessLookupError:
        pass


def run_attempt(record: dict[str, Any], directory: Path) -> int:
    directory.mkdir(parents=True, exist_ok=False)
    started = utc_now()
    launch_error = None
    timeout_error = None
    try:
        proc = subprocess.Popen(
            record["argv"], cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8", errors="replace",
            start_new_session=True,
        )
        try:
            stdout, stderr = proc.communicate(timeout=record["timeout_seconds"])
            returncode = proc.returncode
        except subprocess.TimeoutExpired:
            signal_process_group(proc, signal.SIGTERM)
            try:
                stdout, stderr = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                signal_process_group(proc, signal.SIGKILL)
                stdout, stderr = proc.communicate()
            returncode = 124
            stderr += f"\nattempt timed out after {record['timeout_seconds']} seconds\n"
            timeout_error = {"seconds": record["timeout_seconds"], "process_group_terminated": True}
        except BaseException:
            signal_process_group(proc, signal.SIGTERM)
            try:
                proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                signal_process_group(proc, signal.SIGKILL)
                proc.communicate()
            raise
    except OSError as error:
        returncode, stdout, stderr = 127, "", f"launch error: {error}\n"
        launch_error = repr(error)
    write_text_once(directory / "stdout.txt", stdout)
    write_text_once(directory / "stderr.txt", stderr)
    write_json_once(directory / "receipt.json", {
        "schema": "cpu-baseline-aa-v5-attempt/v1", "record": record,
        "started_at": started, "finished_at": utc_now(), "returncode": returncode,
        "launch_error": launch_error, "timeout_error": timeout_error,
        "stdout_sha256": sha256(directory / "stdout.txt"),
        "stderr_sha256": sha256(directory / "stderr.txt"),
    })
    return returncode


def verify_bootstrap_identity(data: dict[str, Any]) -> None:
    required = {
        item["path"]: item
        for item in data["extensions"]["cpu_baseline_aa_v5"]["required_files"]
    }
    for path in (PYTHON, PROTOCOL_TOOL, PROTOCOL_SCHEMA, EXPORT_SCHEMA):
        item = required.get(str(path))
        if item is None or not path.is_file() or path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            raise RuntimeError(f"protocol validation bootstrap identity mismatch: {path}")


def validate_protocol(protocol: Path) -> dict[str, Any]:
    data = json.loads(protocol.read_text(encoding="utf-8"))
    verify_bootstrap_identity(data)
    subprocess.run(
        [str(PYTHON), str(PROTOCOL_TOOL), "validate", str(protocol)],
        check=True, timeout=60,
    )
    freeze = data.get("freeze", {})
    if freeze.get("status") != "frozen" or not re.fullmatch(r"[0-9a-f]{64}", str(freeze.get("protocol_sha256"))):
        raise RuntimeError("v5 protocol is not canonically frozen")
    observed = subprocess.check_output(
        [str(PYTHON), str(PROTOCOL_TOOL), "hash", str(protocol)], text=True,
        timeout=60,
    ).strip()
    if observed != freeze["protocol_sha256"]:
        raise RuntimeError("v5 protocol canonical hash mismatch")
    ext = data["extensions"]["cpu_baseline_aa_v5"]
    if sha256(RUNNER) != ext["runner_sha256"] or sha256(ANALYZER) != data["analysis_plan"]["script"]["sha256"]:
        raise RuntimeError("runner/analyzer hash differs from the frozen protocol")
    plan = build_plan()
    if plan["digests"] != ext["command_plan_digests"]:
        raise RuntimeError("generated command-plan digest differs from the frozen protocol")
    return data


def verify_identity(protocol: dict[str, Any]) -> None:
    ext = protocol["extensions"]["cpu_baseline_aa_v5"]
    for item in ext["required_files"]:
        path = Path(item["path"])
        if not path.is_file() or path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            raise RuntimeError(f"required identity mismatch: {path}")
        if item.get("mode") and f"{path.stat().st_mode & 0o777:04o}" != item["mode"]:
            raise RuntimeError(f"required mode mismatch: {path}")
    sources = sorted(path.name for path in Path("/sys/bus/event_source/devices").iterdir())
    if sources != ["breakpoint", "msr", "software"]:
        raise RuntimeError(f"perf event-source inventory changed: {sources}")
    if Path("/proc/sys/kernel/perf_event_paranoid").read_text().strip() != "2":
        raise RuntimeError("kernel.perf_event_paranoid changed")
    if Path("/sys/devices/system/cpu/online").read_text().strip() != "0-4":
        raise RuntimeError("online CPU inventory changed")
    for relative in ("wall-1t", "wall-4t", "profiles"):
        if (V4_ROOT / relative).exists():
            raise RuntimeError(f"v4 acquired affected data after the v5 amendment: {relative}")


def select_perf_record_from_counts(counts: dict[str, int]) -> list[str]:
    if set(counts) != set(C_IDS) or any(not isinstance(value, int) or value < 0 for value in counts.values()):
        raise ValueError("selection requires one nonnegative integer Ir count for every C cell")
    ranked = sorted(C_IDS, key=lambda kernel: (-counts[kernel], kernel))[:5]
    return [*FIXED_RECORD_IDS, *ranked]


def expected_wall_fingerprint(run_root: Path, kernel: str) -> str | None:
    language = "rust" if kernel in RUST_IDS else "c"
    values: set[str] = set()
    for panel in ("1t", "4t"):
        path = run_root / f"wall-{panel}/{language}/compare/compare.json"
        if not path.is_file():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))["raw"][kernel]
            for arm in ("A", "B"):
                for row in raw[arm]:
                    value = row.get("fingerprint")
                    if isinstance(value, str) and value:
                        values.add(value)
        except (KeyError, TypeError, json.JSONDecodeError):
            return None
    return next(iter(values)) if len(values) == 1 else None


def validated_callgrind_result(
    run_root: Path, record: dict[str, Any], expected_fingerprint: str | None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Read a Callgrind result only after every bound receipt agrees."""
    attempt = run_root / (
        f"orchestration/attempts/callgrind-{record['ordinal']:03d}-{record['arm']}"
    )
    output = Path(record["output"])
    required = {
        "outer": attempt / "receipt.json", "command": output / "command.json",
        "inner": output / "receipt.json", "status": output / "status.txt",
        "result": output / "result.json",
    }
    if any(not path.is_file() for path in required.values()):
        return None, "missing outer/inner Callgrind evidence"
    try:
        outer = json.loads(required["outer"].read_text(encoding="utf-8"))
        command = json.loads(required["command"].read_text(encoding="utf-8"))
        inner = json.loads(required["inner"].read_text(encoding="utf-8"))
        row = json.loads(required["result"].read_text(encoding="utf-8"))
        status = required["status"].read_text(encoding="utf-8").strip()
    except (OSError, json.JSONDecodeError) as error:
        return None, f"malformed Callgrind evidence: {error}"
    if outer.get("record") != record or outer.get("returncode") != 0:
        return None, "outer Callgrind receipt is not the planned successful attempt"
    expected_argv = callgrind_inner_argv(binary_for(record["kernel"]), record["kernel"])
    if command != {"schema": "cpu-baseline-aa-v5-callgrind-command/v1", "argv": expected_argv}:
        return None, "inner Callgrind argv differs from the frozen invocation"
    if (
        inner.get("schema") != "cpu-baseline-aa-v5-callgrind-receipt/v1"
        or inner.get("child_returncode") != 0
        or inner.get("effective_returncode") != 0
        or inner.get("parse_error") is not None
        or status != "0"
    ):
        return None, "inner Callgrind status is not a parsed success"
    if (
        row.get("id") != record["kernel"]
        or not isinstance(row.get("ir"), int)
        or row["ir"] < 0
        or not isinstance(row.get("fingerprint"), str)
        or not row["fingerprint"]
    ):
        return None, "Callgrind result cell, fingerprint, or Ir is invalid"
    if expected_fingerprint is not None and row["fingerprint"] != expected_fingerprint:
        return None, "Callgrind fingerprint differs from the complete wall panel"
    return row, None


def choose_perf_record() -> tuple[list[dict[str, Any]] | None, dict[str, Any]]:
    counts: dict[str, int] = {}
    by_key = {(row["kernel"], row["arm"]): row for row in callgrind_commands()}
    missing: list[str] = []
    for kernel in C_IDS:
        expected_fingerprint = expected_wall_fingerprint(RUN_ROOT, kernel)
        row, _ = validated_callgrind_result(
            RUN_ROOT, by_key[(kernel, "A")], expected_fingerprint,
        )
        if row is None or expected_fingerprint is None:
            missing.append(kernel)
        else:
            counts[kernel] = row["ir"]
    if missing:
        return None, {"status": "not_attempted_missing_c_callgrind_a", "missing": missing}
    selected = select_perf_record_from_counts(counts)
    commands = [perf_record_command(i, kernel) for i, kernel in enumerate(selected, 1)]
    return commands, {
        "status": "selected", "selected": selected, "commands_sha256": digest_value(commands),
        "c_baseline_ir": dict(sorted(counts.items())),
    }


def write_terminal_once(status: str, **fields: Any) -> None:
    orchestration = RUN_ROOT / "orchestration"
    path = orchestration / "terminal.json"
    if path.exists():
        return
    write_json_once(path, {
        "schema": "cpu-baseline-aa-v5-terminal/v1", "status": status,
        "finished_at": utc_now(), "continuation": "forbidden", **fields,
    })


def emit_terminal_analysis(protocol_path: Path) -> None:
    subprocess.run([
        str(PYTHON), str(ANALYZER), "--protocol", str(protocol_path),
        "--run-root", str(RUN_ROOT),
    ], cwd=REPO, timeout=ATTEMPT_TIMEOUT_SECONDS)


def execute_campaign(protocol_path: Path, protocol: dict[str, Any]) -> int:
    orchestration = RUN_ROOT / "orchestration"
    orchestration.mkdir(mode=0o700)
    plan = build_plan()
    write_json_once(orchestration / "command-plan.json", plan)
    with (orchestration / "processes-before.txt").open("x", encoding="utf-8") as stream:
        subprocess.run(
            ["ps", "-eLo", "pid,ppid,lwp,psr,stat,etime,pcpu,pmem,comm,args"],
            check=True, stdout=stream, text=True, timeout=60,
        )
    write_json_once(orchestration / "start.json", {
        "schema": "cpu-baseline-aa-v5-start/v1", "started_at": utc_now(),
        "protocol_sha256": protocol["freeze"]["protocol_sha256"],
        "plan_sha256": sha256(orchestration / "command-plan.json"),
        "plan_preimage_sha256": plan["digests"]["plan_preimage"],
        "other_cpu_work_paused_confirmed": True, "resume_policy": "forbidden",
    })

    for index, record in enumerate(plan["wall"], 1):
        if run_attempt(record, orchestration / f"attempts/wall-{index:02d}-{record['id']}") != 0:
            write_terminal_once("wall_command_failed", record=record)
            emit_terminal_analysis(protocol_path)
            return 1
    gate = subprocess.run([
        str(PYTHON), str(ANALYZER), "--protocol", str(protocol_path),
        "--run-root", str(RUN_ROOT), "--wall-gate-only",
    ], cwd=REPO, timeout=ATTEMPT_TIMEOUT_SECONDS)
    if gate.returncode != 0:
        write_terminal_once("wall_gate_failed", returncode=gate.returncode)
        emit_terminal_analysis(protocol_path)
        return 1

    (RUN_ROOT / "profiles/callgrind").mkdir(parents=True, exist_ok=False)
    (RUN_ROOT / "profiles/perf-stat").mkdir(parents=True, exist_ok=False)
    for phase in ("callgrind", "perf_stat"):
        for record in plan[phase]:
            run_attempt(record, orchestration / f"attempts/{phase}-{record['ordinal']:03d}-{record['arm']}")

    commands, selection = choose_perf_record()
    write_json_once(orchestration / "perf-record-selection.json", selection)
    if commands is not None:
        (RUN_ROOT / "profiles/perf-record").mkdir(parents=True, exist_ok=False)
        write_json_once(orchestration / "perf-record-command-plan.json", commands)
        for record in commands:
            run_attempt(record, orchestration / f"attempts/perf-record-{record['ordinal']:03d}")

    write_json_once(orchestration / "complete.json", {"status": "orchestration_complete", "finished_at": utc_now()})
    analysis = subprocess.run([
        str(PYTHON), str(ANALYZER), "--protocol", str(protocol_path),
        "--run-root", str(RUN_ROOT),
    ], cwd=REPO, timeout=ATTEMPT_TIMEOUT_SECONDS)
    if analysis.returncode != 0:
        write_terminal_once("analysis_or_export_failed", returncode=analysis.returncode)
    return analysis.returncode


def command_run(options: argparse.Namespace) -> int:
    protocol_path = options.protocol.resolve()
    protocol = validate_protocol(protocol_path)
    verify_identity(protocol)
    if not options.confirm_other_cpu_work_paused:
        raise SystemExit("run requires --confirm-other-cpu-work-paused")
    if RUN_ROOT.exists():
        raise SystemExit(f"refusing existing one-shot run root: {RUN_ROOT}")
    RUN_ROOT.mkdir(parents=True, mode=0o700)
    try:
        return execute_campaign(protocol_path, protocol)
    except KeyboardInterrupt:
        (RUN_ROOT / "orchestration").mkdir(mode=0o700, exist_ok=True)
        write_terminal_once("interrupted_by_operator", error="KeyboardInterrupt")
        return 130
    except Exception as error:  # the sealed root is evidence; never resume it
        (RUN_ROOT / "orchestration").mkdir(mode=0o700, exist_ok=True)
        write_terminal_once(
            "orchestration_exception", error_type=type(error).__name__, error=str(error),
        )
        print(f"cpu baseline A/A v5 terminated: {type(error).__name__}: {error}", file=sys.stderr)
        return 1


def command_callgrind_one(options: argparse.Namespace) -> int:
    output = options.out.resolve()
    if output.exists():
        raise SystemExit(f"refusing existing Callgrind attempt: {output}")
    expected_binary = binary_for(options.kernel).resolve()
    if options.binary.resolve() != expected_binary:
        raise SystemExit(f"binary is not the frozen instrument for {options.kernel}")
    expected_outputs = {
        Path(record["output"]) for record in callgrind_commands()
        if record["kernel"] == options.kernel
    }
    if output not in expected_outputs:
        raise SystemExit("Callgrind output is outside the frozen attempt plan")
    output.mkdir(parents=True)
    argv = callgrind_inner_argv(options.binary, options.kernel)
    write_json_once(output / "command.json", {
        "schema": "cpu-baseline-aa-v5-callgrind-command/v1", "argv": argv,
    })
    started = utc_now()
    proc = subprocess.run(argv, cwd=REPO, capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          env={**os.environ, "RAYON_NUM_THREADS": "1"})
    write_text_once(output / "stdout.txt", proc.stdout)
    write_text_once(output / "stderr.txt", proc.stderr)
    effective_returncode = proc.returncode if proc.returncode >= 0 else 128 - proc.returncode
    receipt = {
        "schema": "cpu-baseline-aa-v5-callgrind-receipt/v1",
        "started_at": started, "finished_at": utc_now(),
        "child_returncode": proc.returncode,
        "effective_returncode": effective_returncode,
        "parse_error": None,
    }
    if proc.returncode == 0:
        try:
            rows = [json.loads(line) for line in proc.stdout.splitlines() if line.startswith("{")]
        except json.JSONDecodeError:
            rows = []
        match = re.search(r"Collected\s*:\s*(\d+)", proc.stderr)
        if len(rows) != 1 or match is None:
            receipt["parse_error"] = "expected one JSON row and one Callgrind Collected count"
            receipt["effective_returncode"] = 2
        else:
            row = rows[0]
            row["ir"] = int(match.group(1))
            write_json_once(output / "result.json", row)
    write_text_once(output / "status.txt", f"{receipt['effective_returncode']}\n")
    write_json_once(output / "receipt.json", receipt)
    return receipt["effective_returncode"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--out", type=Path)
    plan.set_defaults(func=lambda options: command_plan(options))
    run = sub.add_parser("run")
    run.add_argument("--protocol", type=Path, required=True)
    run.add_argument("--confirm-other-cpu-work-paused", action="store_true")
    run.set_defaults(func=command_run)
    one = sub.add_parser("callgrind-one")
    one.add_argument("--binary", type=Path, required=True)
    one.add_argument("--kernel", choices=ALL_IDS, required=True)
    one.add_argument("--out", type=Path, required=True)
    one.set_defaults(func=command_callgrind_one)
    return parser.parse_args()


def command_plan(options: argparse.Namespace) -> int:
    plan = build_plan()
    if options.out:
        write_json_once(options.out.resolve(), plan)
    else:
        print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    parsed = parse_args()
    raise SystemExit(parsed.func(parsed))
