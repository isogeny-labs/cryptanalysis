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
import importlib.util
import json
import os
from pathlib import Path
import random
import re
import signal
import subprocess
import sys
import platform
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
RUNTIME_DEPENDENCY_MANIFEST = HERE / "runtime-dependencies-v5.json"
PYTHON_PREFLIGHT = HERE / "python_preflight_v5.sh"
PYTHON_BOOTSTRAP = HERE / "python_bootstrap_v5.py"
PYTHON_CLOSURE = HERE / "python-bootstrap-closure-v5.sha256"
PYTHON_IMPORT_INVENTORY = HERE / "python-import-inventory-v5.txt"
DASH = Path("/bin/dash")
SHA256SUM = Path("/usr/bin/sha256sum")
ISOLATED = Path("/workspace/crypto/target/release/isolated_bench")
PERFINDEX = REPO / "scripts/perf/perfindex.py"
VALGRIND = Path("/workspace/.tools/valgrind/bin/valgrind")
PERF = Path("/workspace/.tools/perf/usr/bin/perf")
PERF_LIB = "/workspace/.tools/perf/usr/lib/x86_64-linux-gnu"
SYSTEM_ENV = Path("/usr/bin/env")
TASKSET = Path("/usr/bin/taskset")
PS = Path("/usr/bin/ps")
BASE_PATH = "/workspace/.tools/rustup/toolchains/stable-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin"
RUST_BINARY = V4_ROOT / "build/base-rust/perfbench"
C_BINARY = V4_ROOT / "build/base-c/ca_perfbench"
RUST_BINARY_SHA256 = "b066d0d8fefac4dd3b3891ab4804e77046302ceb2b86362095a65b632c7c8c37"
C_BINARY_SHA256 = "6d9f3ba6845b47c01d374346a1b87ce6147a09c39fba94d5c2d06a2a2bbcd97d"
RUST_REGISTRY_SHA256 = "b225091d89a02e7400b01bb7704c1f358192049753d4bc279d70dcb352f194a0"
C_REGISTRY_SHA256 = "eafa8c3f389a88115f05ba1c5b602fc3b199cc0a6c80ed71432917c59cc97d44"
PERFINDEX_SHA256 = "28084cd77fe28d3b031f4dc1474241ee051b2072c7b62dc7a17e0049c3e3674f"
ANALYZER = HERE / "analyze_cpu_baseline_aa_v5.py"
RUNNER = Path(__file__).resolve()
ATTEMPT_TIMEOUT_SECONDS = 86_400
CLOSED_BOOTSTRAP_ENV = "CPU_V5_CLOSED_BOOTSTRAP"
PERF_CONFIG_ENV = (
    "PERF_CONFIG=/dev/null", "PERF_CONFIG_NOSYSTEM=1", "PERF_CONFIG_NOGLOBAL=1",
)
CLOSED_BOOTSTRAP_ENTRY: dict[str, Any] | None = None

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
PROFILE_IDS = (*sorted(RUST_IDS), *sorted(C_IDS))
FIXED_RECORD_IDS = (
    "gf2_la/rref_random_4940x8357",
    "bool_gb/matrix_f5_deg4_m2_n23",
    "field_ec/f2m_mul_sqr_m163_64k",
)

WALL_SESSION_SPECS = {
    "rust-1t": {"binary": RUST_BINARY, "ids": RUST_IDS, "threads": 1, "taskset": "0", "language": "rust", "panel": "1t"},
    "c-1t": {"binary": C_BINARY, "ids": C_IDS, "threads": 1, "taskset": "0", "language": "c", "panel": "1t"},
    "rust-4t": {"binary": RUST_BINARY, "ids": RUST_IDS, "threads": 4, "taskset": "0-3", "language": "rust", "panel": "4t"},
    "c-4t": {"binary": C_BINARY, "ids": C_IDS, "threads": 4, "taskset": "0-3", "language": "c", "panel": "4t"},
}


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


def observe_identity(path: Path, expected: dict[str, Any] | None = None) -> dict[str, Any]:
    """Observe one frozen path, including a symlink's routing when applicable."""
    observed: dict[str, Any] = {
        "path": str(path), "exists": path.is_file(), "bytes": None,
        "sha256": None, "mode": None,
    }
    if expected is not None:
        for field in ("scope", "group"):
            if field in expected:
                observed[field] = expected[field]
        if "link_target" in expected:
            observed["link_target"] = os.readlink(path) if path.is_symlink() else None
    if path.is_file():
        stat = path.stat()
        observed.update({
            "bytes": stat.st_size, "sha256": sha256(path),
            "mode": f"{stat.st_mode & 0o777:04o}",
        })
    return observed


def safe_id(kernel: str) -> str:
    return kernel.replace("/", "_")


def binary_for(kernel: str) -> Path:
    return RUST_BINARY if kernel in RUST_IDS else C_BINARY


def work_contract(
    session: str, kernel: str, registry_row: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Return the pre-data source/build/registry-bound work contract."""
    spec = WALL_SESSION_SPECS[session]
    payload = {
        "schema": "cpu-baseline-aa-v5-work-contract/v1",
        "source_commit": "781722ef89e74b62079d2bc0cb82217061ac188c",
        "session": session, "kernel": kernel, "registry": registry_row,
        "binary": str(spec["binary"]),
        "binary_sha256": (
            RUST_BINARY_SHA256 if spec["language"] == "rust" else C_BINARY_SHA256
        ),
        "threads": spec["threads"], "taskset": spec["taskset"],
        "samples": 5, "max_seconds": 2.0, "rounds": 6,
        "seed": 20260926, "exact": True,
    }
    return digest_value(payload), payload


def reserve_prefix(isolation: Path, label: str) -> list[str]:
    return [
        str(ISOLATED), "reserve", "--lock", str(GLOBAL_LOCK), "--wait",
        "--cpus", "0-3", "--settle", "2", "--max-other-cpu", "0.10",
        "--max-psi", "5", "--period", "5", "--out", str(isolation),
        "--label", label, "--",
    ]


def clean_env(*extra: str, path: str = BASE_PATH) -> list[str]:
    return [
        str(SYSTEM_ENV), "-i", f"PATH={path}", "LC_ALL=C", "LANG=C", "TZ=UTC",
        "PYTHONHASHSEED=0", "PYTHONCOERCECLOCALE=0", "PYTHONUTF8=1", *extra,
    ]


def closed_python_command(
    target: Path, *arguments: str, profile: str = "base",
) -> list[str]:
    """Return an inherited-nothing, pre-import-verified Python invocation."""
    if profile == "base":
        path, extra = BASE_PATH, ()
    elif profile == "wall-1":
        path, extra = BASE_PATH, (
            "RAYON_NUM_THREADS=1", "OMP_NUM_THREADS=1", "OPENBLAS_NUM_THREADS=1",
        )
    elif profile == "wall-4":
        path, extra = BASE_PATH, (
            "RAYON_NUM_THREADS=4", "OMP_NUM_THREADS=4", "OPENBLAS_NUM_THREADS=1",
        )
    elif profile == "callgrind-1":
        path, extra = "/workspace/.tools/valgrind/bin:/usr/bin:/bin", (
            "RAYON_NUM_THREADS=1", "OMP_NUM_THREADS=1", "OPENBLAS_NUM_THREADS=1",
        )
    else:
        raise ValueError(f"unknown closed Python profile: {profile}")
    return clean_env(*extra, path=path) + [
        str(DASH), str(PYTHON_PREFLIGHT), profile, str(target), *arguments,
    ]


def bootstrap_environment(profile: str) -> dict[str, str]:
    """Return the exact target environment installed by the frozen router."""
    environment = {
        "LANG": "C", "LC_ALL": "C", "PATH": BASE_PATH,
        "PYTHONCOERCECLOCALE": "0", "PYTHONHASHSEED": "0",
        "PYTHONUTF8": "1", "TZ": "UTC",
        CLOSED_BOOTSTRAP_ENV: f"cpu-baseline-aa-v5/{profile}",
    }
    if profile == "wall-1":
        environment.update({
            "RAYON_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
        })
    elif profile == "wall-4":
        environment.update({
            "RAYON_NUM_THREADS": "4", "OMP_NUM_THREADS": "4",
            "OPENBLAS_NUM_THREADS": "1",
        })
    elif profile == "callgrind-1":
        environment.update({
            "PATH": "/workspace/.tools/valgrind/bin:/usr/bin:/bin",
            "RAYON_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
        })
    elif profile != "base":
        raise ValueError(f"unknown closed Python profile: {profile}")
    return environment


def expected_bootstrap_entry(
    profile: str, target: Path, arguments: list[str],
) -> dict[str, Any]:
    target = target.resolve()
    process_argv = [
        str(PYTHON), "-S", "-B", "-P", "-X", "pycache_prefix=/dev/null",
        str(PYTHON_BOOTSTRAP), profile, str(target), *arguments,
    ]
    return {
        "schema": "cpu-baseline-aa-v5-bootstrap-entry/v1",
        "profile": profile, "target": str(target),
        "process_argv": process_argv,
        "process_argv_sha256": digest_value(process_argv),
        "environment": bootstrap_environment(profile),
    }


def require_closed_bootstrap(profile: str) -> None:
    """Prove and consume the external-preflight/router entry before child launch."""
    global CLOSED_BOOTSTRAP_ENTRY
    expected = f"cpu-baseline-aa-v5/{profile}"
    observed = os.environ.get(CLOSED_BOOTSTRAP_ENV)
    if observed != expected or dict(os.environ) != bootstrap_environment(profile):
        raise SystemExit("CPU v5 target was not entered through its frozen Python bootstrap")
    target = Path(sys.argv[0]).resolve()
    entry = expected_bootstrap_entry(profile, target, sys.argv[1:])
    try:
        process_argv = [
            part.decode("utf-8", "strict")
            for part in Path("/proc/self/cmdline").read_bytes().split(b"\0") if part
        ]
    except (OSError, UnicodeDecodeError) as error:
        raise SystemExit(f"CPU v5 cannot prove its bootstrap process argv: {error}")
    if process_argv != entry["process_argv"]:
        raise SystemExit("CPU v5 process argv does not prove the frozen external preflight route")
    CLOSED_BOOTSTRAP_ENTRY = entry
    os.environ.pop(CLOSED_BOOTSTRAP_ENV)


def wall_environment(threads: int) -> dict[str, str]:
    """The complete, inherited-nothing environment of a wall session."""
    return {
        "LANG": "C", "LC_ALL": "C", "OMP_NUM_THREADS": str(threads),
        "OPENBLAS_NUM_THREADS": "1", "PATH": BASE_PATH,
        "PYTHONCOERCECLOCALE": "0", "PYTHONHASHSEED": "0",
        "PYTHONUTF8": "1", "RAYON_NUM_THREADS": str(threads), "TZ": "UTC",
    }


def wall_commands() -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    for session, spec in WALL_SESSION_SPECS.items():
        language = spec["language"]
        panel = spec["panel"]
        output = RUN_ROOT / f"wall-{panel}/{language}/compare"
        isolation = RUN_ROOT / f"wall-{panel}/{language}/isolation.jsonl"
        argv = reserve_prefix(isolation, f"cpu-baseline-aa-v5-{session}")
        argv += closed_python_command(
            RUNNER, "wall-session", "--session", session, "--out", str(output),
            profile=f"wall-{spec['threads']}",
        )
        commands.append({"id": session, "argv": argv, "timeout_seconds": ATTEMPT_TIMEOUT_SECONDS})
    return commands


def callgrind_commands() -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    ordinal = 0
    for kernel in PROFILE_IDS:
        for arm in ("A", "B"):
            ordinal += 1
            stem = f"{ordinal:03d}_{arm}_{safe_id(kernel)}"
            isolation = RUN_ROOT / f"profiles/callgrind/{stem}.isolation.jsonl"
            output = RUN_ROOT / f"profiles/callgrind/{stem}"
            argv = reserve_prefix(isolation, f"cpu-baseline-aa-v5-callgrind-{ordinal:03d}-{arm}")
            argv += [str(TASKSET), "-c", "0"] + closed_python_command(
                RUNNER, "callgrind-one", "--binary", str(binary_for(kernel)),
                "--kernel", kernel, "--out", str(output), profile="callgrind-1",
            )
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
            argv += clean_env(
                f"LD_LIBRARY_PATH={PERF_LIB}", "RAYON_NUM_THREADS=1",
                "OMP_NUM_THREADS=1", "OPENBLAS_NUM_THREADS=1",
                *PERF_CONFIG_ENV,
                path="/usr/bin:/bin",
            ) + [
                str(TASKSET), "-c", "0",
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
    argv += clean_env(
        f"LD_LIBRARY_PATH={PERF_LIB}", "RAYON_NUM_THREADS=1",
        "OMP_NUM_THREADS=1", "OPENBLAS_NUM_THREADS=1",
        *PERF_CONFIG_ENV,
        path="/usr/bin:/bin",
    ) + [
        str(TASKSET), "-c", "0", str(PERF),
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
    """Frozen instr_one semantics with absolute/config-closed Valgrind routing."""
    return [
        str(VALGRIND), "--command-line-only=yes", "--tool=callgrind",
        "--callgrind-out-file=/dev/null",
        "--instr-atstart=no", str(binary), "run", "--filter", kernel,
        "--exact", "--instr",
    ]


def callgrind_requires_registry_prelude(record: dict[str, Any]) -> bool:
    ids = RUST_IDS if record["kernel"] in RUST_IDS else C_IDS
    return record["arm"] == "A" and record["kernel"] == sorted(ids)[0]


def validate_callgrind_registry_prelude(
    output: Path, record: dict[str, Any],
) -> str | None:
    if not callgrind_requires_registry_prelude(record):
        return None
    language = "rust" if record["kernel"] in RUST_IDS else "c"
    binary = binary_for(record["kernel"])
    expected_rows = [
        json.loads(line) for line in (V4_ROOT / f"registry/{language}.jsonl").read_text().splitlines()
        if line.strip()
    ]
    if language == "rust":
        expected_rows = [row for row in expected_rows if row.get("tier") == "Quick"]
    argv = [str(binary), "list"] + (["--full"] if language == "c" else [])
    for ordinal, role in enumerate(("base", "cand"), 1):
        try:
            started = json.loads((output / f"prelude/{ordinal:02d}-{role}.started.json").read_text())
            receipt = json.loads((output / f"prelude/{ordinal:02d}-{role}.json").read_text())
            stdout_rows = [
                json.loads(line) for line in receipt.get("stdout", "").splitlines()
                if line.startswith("{")
            ]
        except (OSError, json.JSONDecodeError) as error:
            return f"missing or malformed {language} Callgrind registry prelude: {error}"
        if (
            started.get("argv") != argv or started.get("ordinal") != ordinal
            or started.get("role") != role or receipt.get("argv") != argv
            or receipt.get("started_at") != started.get("started_at")
            or receipt.get("child_returncode") != 0
            or receipt.get("effective_returncode") != 0
            or receipt.get("timed_out") is not False
            or receipt.get("parse_error") is not None
            or receipt.get("rows") != expected_rows or stdout_rows != expected_rows
        ):
            return f"{language} Callgrind registry prelude differs from frozen aggregate semantics"
    return None


def wall_schedule(session: str) -> list[dict[str, Any]]:
    spec = WALL_SESSION_SPECS[session]
    rng = random.Random(20260926)
    kernels = sorted(spec["ids"])
    schedule: list[dict[str, Any]] = []
    for round_index in range(6):
        order = kernels[:]
        rng.shuffle(order)
        arms = ("A", "B") if round_index % 2 == 0 else ("B", "A")
        for kernel in order:
            schedule.append({"round": round_index, "kernel": kernel, "arms": arms})
    return schedule


def export_seed_table() -> list[dict[str, Any]]:
    """Canonical descriptive execution cells used by export (replicates are 1-based)."""
    return [
        {"arm": arm, "instance_id": kernel, "replicate": replicate, "seed": 20260926}
        for arm in ("base-1t", "base-aa-1t", "base-4t", "base-aa-4t")
        for kernel in ALL_IDS
        for replicate in range(1, 7)
    ]


def load_frozen_perfindex():
    spec = importlib.util.spec_from_file_location("cpu_v5_runner_perfindex", PERFINDEX)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen perfindex")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json_durable_once(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8") + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        offset = 0
        while offset < len(data):
            offset += os.write(descriptor, data[offset:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(parent)
    finally:
        os.close(parent)


def append_json_durable(path: Path, value: Any) -> None:
    data = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8") + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_APPEND)
    try:
        offset = 0
        while offset < len(data):
            offset += os.write(descriptor, data[offset:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_bytes_durable_once(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        offset = 0
        while offset < len(data):
            offset += os.write(descriptor, data[offset:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(parent)
    finally:
        os.close(parent)


def write_text_durable_once(path: Path, value: str) -> None:
    write_bytes_durable_once(path, value.encode("utf-8"))


def create_empty_durable(path: Path) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(parent)
    finally:
        os.close(parent)


def run_wall_child(argv: list[str], timeout_seconds: int = 1800) -> tuple[int, str, str, bool]:
    proc = subprocess.Popen(
        argv, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace",
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout_seconds)
        return proc.returncode, stdout, stderr, False
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            stdout, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
        return 124, stdout, stderr + f"\ninvocation timed out after {timeout_seconds} seconds\n", True
    except BaseException:
        proc.terminate()
        try:
            proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
        raise


def run_registry_prelude(
    output: Path, spec: dict[str, Any], expected_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]] | None, int]:
    prelude = output / "prelude"
    prelude.mkdir(mode=0o700)
    selected: list[dict[str, Any]] | None = None
    for ordinal, role in enumerate(("base", "cand"), 1):
        argv = [str(spec["binary"]), "list"]
        if spec["language"] == "c":
            argv.append("--full")
        started = utc_now()
        write_json_durable_once(prelude / f"{ordinal:02d}-{role}.started.json", {
            "schema": "cpu-baseline-aa-v5-registry-prelude-start/v1",
            "ordinal": ordinal, "role": role, "argv": argv, "started_at": started,
        })
        returncode, stdout, stderr, timed_out = run_wall_child(argv)
        rows: list[dict[str, Any]] = []
        parse_error = None
        if returncode == 0:
            try:
                rows = [json.loads(line) for line in stdout.splitlines() if line.startswith("{")]
            except json.JSONDecodeError as error:
                parse_error = str(error)
            if rows != expected_rows:
                parse_error = parse_error or "live registry differs from retained frozen registry"
        effective = returncode if returncode != 0 else (2 if parse_error else 0)
        write_json_durable_once(prelude / f"{ordinal:02d}-{role}.json", {
            "schema": "cpu-baseline-aa-v5-registry-prelude/v1",
            "ordinal": ordinal, "role": role, "argv": argv,
            "started_at": started, "finished_at": utc_now(),
            "child_returncode": returncode, "effective_returncode": effective,
            "timed_out": timed_out, "parse_error": parse_error,
            "stdout": stdout, "stderr": stderr, "rows": rows,
        })
        if effective != 0:
            return None, effective
        selected = rows
    return selected, 0


def command_wall_session(options: argparse.Namespace) -> int:
    spec = WALL_SESSION_SPECS[options.session]
    expected_out = RUN_ROOT / f"wall-{spec['panel']}/{spec['language']}/compare"
    output = options.out.resolve()
    if output != expected_out or output.exists():
        raise SystemExit(f"wall-session output is not the new frozen path: {output}")
    output.mkdir(parents=True, mode=0o700)
    attempts_dir = output / "attempts"
    attempts_dir.mkdir(mode=0o700)
    journal = output / "attempts.jsonl"
    create_empty_durable(journal)
    events = output / "events.jsonl"
    create_empty_durable(events)
    perf = load_frozen_perfindex()
    registry_path = V4_ROOT / f"registry/{spec['language']}.jsonl"
    expected_registry_rows = [
        json.loads(line) for line in registry_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if spec["language"] == "rust":
        expected_registry_rows = [row for row in expected_registry_rows if row.get("tier") == "Quick"]
    observed_environment = dict(sorted(os.environ.items()))
    expected_environment = wall_environment(spec["threads"])
    environment_error = None if observed_environment == expected_environment else (
        "wall-session environment differs from the frozen inherited-nothing environment"
    )
    write_json_durable_once(output / "session-start.json", {
        "schema": "cpu-baseline-aa-v5-wall-session-start/v1", "session": options.session,
        "binary": str(spec["binary"]), "environment": observed_environment,
        "binary_sha256": sha256(spec["binary"]),
        "registry_sha256": sha256(registry_path),
        "perfindex_sha256": sha256(PERFINDEX), "started_at": utc_now(),
        "environment_error": environment_error,
    })
    if environment_error is not None:
        return 2
    selected_rows, prelude_status = run_registry_prelude(output, spec, expected_registry_rows)
    if selected_rows is None:
        return prelude_status
    registry = {row["id"]: row for row in selected_rows}
    kernels = [registry[kernel] for kernel in sorted(spec["ids"])]
    raw = {kernel: {"A": [], "B": [], "A2": []} for kernel in sorted(spec["ids"])}
    schedule = wall_schedule(options.session)
    host = perf.host_manifest()
    write_json_durable_once(output / "session.json", {
        "schema": "cpu-baseline-aa-v5-wall-session/v1", "session": options.session,
        "binary": str(spec["binary"]), "threads": spec["threads"],
        "taskset": spec["taskset"], "rounds": 6, "samples": 5,
        "max_seconds": 2.0, "invocation_timeout_seconds": 1800,
        "schedule_sha256": digest_value(schedule),
        "environment": observed_environment, "host": host,
        "binary_sha256": sha256(spec["binary"]),
        "registry_sha256": sha256(registry_path),
        "perfindex_sha256": sha256(PERFINDEX),
    })
    sequence = 0
    for item in schedule:
        completed_pair: list[tuple[str, dict[str, Any]]] = []
        for arm in item["arms"]:
            sequence += 1
            argv = [
                str(TASKSET), "-c", spec["taskset"], str(spec["binary"]),
                "run", "--filter", item["kernel"], "--exact", "--samples", "5",
                "--max-seconds", "2.0",
            ]
            started = utc_now()
            stem = f"{sequence:04d}_{arm}_{safe_id(item['kernel'])}"
            started_receipt = {
                "schema": "cpu-baseline-aa-v5-wall-attempt-start/v1",
                "event": "started", "sequence": sequence, "session": options.session,
                "round": item["round"], "kernel": item["kernel"], "arm": arm,
                "argv": argv, "started_at": started,
            }
            write_json_durable_once(attempts_dir / f"{stem}.started.json", started_receipt)
            append_json_durable(events, started_receipt)
            returncode, stdout, stderr, timed_out = run_wall_child(argv)
            parsed: list[dict[str, Any]] = []
            parse_error = None
            if returncode == 0:
                try:
                    parsed = [json.loads(line) for line in stdout.splitlines() if line.startswith("{")]
                except json.JSONDecodeError as error:
                    parse_error = str(error)
                if len(parsed) != 1 or parsed[0].get("id") != item["kernel"]:
                    parse_error = parse_error or "expected exactly one JSON row for the planned kernel"
            effective = returncode if returncode != 0 else (2 if parse_error else 0)
            if effective == 0:
                parsed[0]["round"] = item["round"]
            receipt = {
                "schema": "cpu-baseline-aa-v5-wall-attempt/v1",
                "sequence": sequence, "session": options.session,
                "round": item["round"], "kernel": item["kernel"], "arm": arm,
                "argv": argv, "started_at": started, "finished_at": utc_now(),
                "child_returncode": returncode, "effective_returncode": effective,
                "timed_out": timed_out, "parse_error": parse_error,
                "stdout": stdout, "stderr": stderr,
                "row": parsed[0] if effective == 0 else None,
            }
            receipt["event"] = "finished"
            attempt_path = attempts_dir / f"{stem}.json"
            write_json_durable_once(attempt_path, receipt)
            append_json_durable(journal, receipt)
            append_json_durable(events, receipt)
            if effective != 0:
                return effective
            row = parsed[0]
            raw[item["kernel"]][arm].append(row)
            completed_pair.append((arm, row))
        print(
            f"round {item['round'] + 1}/6 {item['kernel']}: "
            + " ".join(f"{arm}={row['median_ns'] / 1e6:.3f}ms" for arm, row in completed_pair),
            file=sys.stderr, flush=True,
        )
    rng = random.Random(20260926)
    for _ in range(6):
        order = kernels[:]
        rng.shuffle(order)
    summary = perf.summarize(kernels, raw, json.loads((REPO / "docs/perf/weights.json").read_text())["areas"], rng)
    host["loadavg_end"] = os.getloadavg() if hasattr(os, "getloadavg") else None
    summary.update({
        "mode": "wall", "unit": "ms", "base": str(spec["binary"]),
        "cand": str(spec["binary"]), "threads": spec["threads"],
        "samples_per_invocation": 5, "host": host, "raw": raw,
    })
    write_json_durable_once(output / "compare.json", summary)
    write_json_durable_once(output / "session-end.json", {
        "schema": "cpu-baseline-aa-v5-wall-session-end/v1", "session": options.session,
        "finished_at": utc_now(), "binary_sha256": sha256(spec["binary"]),
        "registry_sha256": sha256(registry_path), "perfindex_sha256": sha256(PERFINDEX),
        "completed_invocations": sequence,
    })
    markdown = perf.markdown(summary, "perfbench wall-time comparison")
    write_text_once(output / "compare.md", markdown)
    print(markdown, end="")
    return 0


def build_plan() -> dict[str, Any]:
    wall = wall_commands()
    callgrind = callgrind_commands()
    callgrind_inner = [
        {
            "ordinal": record["ordinal"], "kernel": record["kernel"],
            "arm": record["arm"],
            "argv": callgrind_inner_argv(binary_for(record["kernel"]), record["kernel"]),
            "registry_preludes": (
                [
                    {
                        "ordinal": prelude_ordinal, "role": role,
                        "argv": [str(binary_for(record["kernel"])), "list"]
                        + (["--full"] if record["kernel"] in C_IDS else []),
                    }
                    for prelude_ordinal, role in enumerate(("base", "cand"), 1)
                ]
                if callgrind_requires_registry_prelude(record) else []
            ),
        }
        for record in callgrind
    ]
    perf_stat = perf_stat_commands()
    fixed_record = [perf_record_command(i, kid) for i, kid in enumerate(FIXED_RECORD_IDS, 1)]
    derived_record = perf_record_candidate_templates()
    plan = {
        "schema": "cpu-baseline-aa-v5-command-plan/v1",
        "run_root": str(RUN_ROOT),
        "retained_artifact_root": str(V4_ROOT),
        "wall": wall,
        "callgrind": callgrind,
        "callgrind_inner": callgrind_inner,
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
            "callgrind_inner": digest_value(callgrind_inner),
            "perf_stat": digest_value(perf_stat),
            "perf_record_fixed": digest_value(fixed_record),
            "perf_record_derived_candidates": digest_value(derived_record),
        },
        "counts": {"wall_sessions": 4, "callgrind_attempts": 88, "perf_stat_attempts": 88, "perf_record_attempts": 8},
        "export_seed_table": {
            "count": 1056, "replicate_origin": 1,
            "sha256": digest_value(export_seed_table()),
        },
    }
    # A plan cannot contain its own whole-document hash.  This binds the
    # canonical preimage before the single self-describing digest is added;
    # start.json separately binds the exact persisted command-plan file.
    plan["digests"]["plan_preimage"] = digest_value(plan)
    return plan


def write_json_once(path: Path, value: Any) -> None:
    write_json_durable_once(path, value)


def write_text_once(path: Path, value: str) -> None:
    write_text_durable_once(path, value)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def parse_utc(value: Any) -> dt.datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        return None
    return parsed


def read_optional(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def system_snapshot(label: str) -> dict[str, Any]:
    """Capture the host/cgroup observables promised by the v5 record contract."""
    cpuinfo = read_optional(Path("/proc/cpuinfo")) or ""
    microcode = sorted({
        line.split(":", 1)[1].strip() for line in cpuinfo.splitlines()
        if line.startswith("microcode") and ":" in line
    })
    cgroup_relative = "/"
    for line in (read_optional(Path("/proc/self/cgroup")) or "").splitlines():
        fields = line.split(":", 2)
        if len(fields) == 3 and fields[0] == "0":
            cgroup_relative = fields[2]
            break
    cgroup_root = Path("/sys/fs/cgroup") / cgroup_relative.lstrip("/")
    cgroup_files = {}
    for name in (
        "cpu.max", "cpu.stat", "cpuset.cpus.effective", "cpuset.mems.effective",
        "memory.current", "memory.events", "memory.events.local", "memory.high",
        "memory.max", "memory.swap.current", "memory.swap.max", "pids.current",
        "pids.max",
    ):
        cgroup_files[name] = read_optional(cgroup_root / name)
    governors = {
        path.name: read_optional(path / "cpufreq/scaling_governor")
        for path in sorted(Path("/sys/devices/system/cpu").glob("cpu[0-9]*"))
    }
    frequencies = {
        path.name: {
            name: read_optional(path / f"cpufreq/{name}")
            for name in ("scaling_cur_freq", "scaling_min_freq", "scaling_max_freq")
        }
        for path in sorted(Path("/sys/devices/system/cpu").glob("cpu[0-9]*"))
    }
    return {
        "schema": "cpu-baseline-aa-v5-system-snapshot/v1", "label": label,
        "captured_at": utc_now(), "platform": platform.platform(),
        "uname": list(platform.uname()), "affinity": sorted(os.sched_getaffinity(0)),
        "online_cpus": read_optional(Path("/sys/devices/system/cpu/online")),
        "smt_active": read_optional(Path("/sys/devices/system/cpu/smt/active")),
        "smt_control": read_optional(Path("/sys/devices/system/cpu/smt/control")),
        "numa_online": read_optional(Path("/sys/devices/system/node/online")),
        "microcode": microcode, "governors": governors, "frequencies": frequencies,
        "loadavg": read_optional(Path("/proc/loadavg")),
        "proc_stat": read_optional(Path("/proc/stat")),
        "proc_meminfo": read_optional(Path("/proc/meminfo")),
        "proc_interrupts": read_optional(Path("/proc/interrupts")),
        "proc_softirqs": read_optional(Path("/proc/softirqs")),
        "pressure": {
            name: read_optional(Path(f"/proc/pressure/{name}"))
            for name in ("cpu", "io", "memory")
        },
        "self_cgroup": read_optional(Path("/proc/self/cgroup")),
        "cgroup_path": str(cgroup_root), "cgroup": cgroup_files,
    }


def write_system_snapshot_once(label: str) -> None:
    path = RUN_ROOT / f"orchestration/system-{label}.json"
    if not path.exists():
        write_json_durable_once(path, system_snapshot(label))


def signal_process_group(proc: subprocess.Popen[str], sig: signal.Signals) -> None:
    try:
        os.killpg(proc.pid, sig)
    except ProcessLookupError:
        pass


def run_attempt(record: dict[str, Any], directory: Path) -> int:
    directory.mkdir(parents=True, exist_ok=False)
    started = utc_now()
    write_json_durable_once(directory / "started.json", {
        "schema": "cpu-baseline-aa-v5-attempt-start/v1", "record": record,
        "started_at": started,
    })
    launch_error = None
    timeout_error = None
    try:
        proc = subprocess.Popen(
            record["argv"], cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8", errors="replace",
            start_new_session=True,
        )
        write_json_durable_once(directory / "launched.json", {
            "schema": "cpu-baseline-aa-v5-attempt-launch/v1", "record": record,
            "started_at": started, "pid": proc.pid, "process_group": proc.pid,
        })
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
    write_text_durable_once(directory / "stdout.txt", stdout)
    write_text_durable_once(directory / "stderr.txt", stderr)
    write_json_durable_once(directory / "receipt.json", {
        "schema": "cpu-baseline-aa-v5-attempt/v1", "record": record,
        "started_at": started, "finished_at": utc_now(), "returncode": returncode,
        "launch_error": launch_error, "timeout_error": timeout_error,
        "stdout_sha256": sha256(directory / "stdout.txt"),
        "stderr_sha256": sha256(directory / "stderr.txt"),
    })
    return returncode


def dependency_manifest_contract(data: dict[str, Any]) -> dict[str, Any]:
    contract = data["extensions"]["cpu_baseline_aa_v5"].get(
        "runtime_dependency_manifest"
    )
    if not isinstance(contract, dict):
        raise RuntimeError("protocol lacks the runtime dependency manifest contract")
    if contract.get("path") != str(RUNTIME_DEPENDENCY_MANIFEST):
        raise RuntimeError("runtime dependency manifest path differs from the frozen path")
    return contract


def load_dependency_manifest(data: dict[str, Any]) -> dict[str, Any]:
    """Load the exact manifest before trusting any of its transitive entries."""
    contract = dependency_manifest_contract(data)
    expected_file = {
        item["path"]: item
        for item in data["extensions"]["cpu_baseline_aa_v5"]["required_files"]
    }.get(str(RUNTIME_DEPENDENCY_MANIFEST))
    observed = observe_identity(RUNTIME_DEPENDENCY_MANIFEST)
    if expected_file is None or any(
        observed.get(field) != expected_file.get(field)
        for field in ("bytes", "sha256", "mode")
    ):
        raise RuntimeError("runtime dependency manifest file identity mismatch")
    try:
        manifest = json.loads(RUNTIME_DEPENDENCY_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"cannot parse runtime dependency manifest: {error}") from error
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if (
        manifest.get("schema") != "cpu-baseline-aa-v5-runtime-dependencies/v1"
        or not isinstance(files, list)
        or any(not isinstance(item, dict) for item in files)
    ):
        raise RuntimeError("runtime dependency manifest violates its frozen schema")
    paths = [item.get("path") for item in files]
    if (
        len(paths) != len(set(paths))
        or any(not isinstance(path, str) or not Path(path).is_absolute() for path in paths)
    ):
        raise RuntimeError("runtime dependency manifest paths are invalid or duplicated")
    if len(files) != contract.get("file_count") or digest_value(files) != contract.get(
        "entries_sha256"
    ):
        raise RuntimeError("runtime dependency manifest entries differ from the protocol")
    group_values = {item.get("group") for item in files}
    if any(not isinstance(group, str) or not group for group in group_values):
        raise RuntimeError("runtime dependency manifest contains an invalid group")
    groups = sorted(group_values)
    counts = {group: sum(item.get("group") == group for item in files) for group in groups}
    group_digests = {
        group: digest_value([item for item in files if item.get("group") == group])
        for group in groups
    }
    if (
        counts != contract.get("groups")
        or group_digests != contract.get("group_entries_sha256")
    ):
        raise RuntimeError("runtime dependency manifest groups differ from the protocol")
    return manifest


def verify_expected_identity(expected: dict[str, Any]) -> None:
    observed = observe_identity(Path(expected["path"]), expected)
    fields = ["bytes", "sha256", "mode"]
    if "link_target" in expected:
        fields.append("link_target")
    if not observed["exists"] or any(
        observed.get(field) != expected.get(field) for field in fields
    ):
        raise RuntimeError(f"required identity mismatch: {expected['path']}")


def verify_bootstrap_identity(data: dict[str, Any]) -> None:
    required = {
        item["path"]: item
        for item in data["extensions"]["cpu_baseline_aa_v5"]["required_files"]
    }
    for path in (
        PYTHON, PROTOCOL_TOOL, PROTOCOL_SCHEMA, EXPORT_SCHEMA,
        PYTHON_PREFLIGHT, PYTHON_BOOTSTRAP, PYTHON_CLOSURE,
        PYTHON_IMPORT_INVENTORY, DASH, SHA256SUM, SYSTEM_ENV,
    ):
        item = required.get(str(path))
        if item is None:
            raise RuntimeError(f"protocol validation bootstrap identity mismatch: {path}")
        verify_expected_identity(item)
    manifest = load_dependency_manifest(data)
    for item in manifest["files"]:
        if item.get("group") in {"python_stdlib", "python_schema_runtime"}:
            verify_expected_identity(item)


def validate_protocol(protocol: Path) -> dict[str, Any]:
    data = json.loads(protocol.read_text(encoding="utf-8"))
    verify_bootstrap_identity(data)
    subprocess.run(
        closed_python_command(PROTOCOL_TOOL, "validate", str(protocol)),
        check=True, timeout=60,
    )
    freeze = data.get("freeze", {})
    if freeze.get("status") != "frozen" or not re.fullmatch(r"[0-9a-f]{64}", str(freeze.get("protocol_sha256"))):
        raise RuntimeError("v5 protocol is not canonically frozen")
    observed = subprocess.check_output(
        closed_python_command(PROTOCOL_TOOL, "hash", str(protocol)),
        text=True, timeout=60,
    ).strip()
    if observed != freeze["protocol_sha256"]:
        raise RuntimeError("v5 protocol canonical hash mismatch")
    ext = data["extensions"]["cpu_baseline_aa_v5"]
    required_runner = [
        item.get("sha256") for item in ext["required_files"]
        if item.get("path") == str(RUNNER)
    ]
    required_analyzer = [
        item.get("sha256") for item in ext["required_files"]
        if item.get("path") == str(ANALYZER)
    ]
    observed_runner = sha256(RUNNER)
    observed_analyzer = sha256(ANALYZER)
    if len(required_runner) != 1 or len({
        ext.get("runner_sha256"), *required_runner, observed_runner,
    }) != 1:
        raise RuntimeError(
            "runner identities differ across extension/required file/observed SHA-256"
        )
    if len(required_analyzer) != 1 or len({
        ext.get("analyzer_sha256"),
        data["analysis_plan"]["script"].get("sha256"),
        *required_analyzer,
        observed_analyzer,
    }) != 1:
        raise RuntimeError(
            "analyzer identities differ across extension/analysis plan/required file/observed SHA-256"
        )
    plan = build_plan()
    if plan["digests"] != ext["command_plan_digests"]:
        raise RuntimeError("generated command-plan digest differs from the frozen protocol")
    return data


def identity_inventory(protocol: dict[str, Any]) -> list[dict[str, Any]]:
    ext = protocol["extensions"]["cpu_baseline_aa_v5"]
    inventory = [
        observe_identity(Path(required["path"]), required)
        for required in ext["required_files"]
    ]
    try:
        manifest = load_dependency_manifest(protocol)
    except RuntimeError:
        manifest = None
    if manifest is not None:
        for expected in manifest["files"]:
            item = dict(expected)
            item["scope"] = "runtime_dependency"
            inventory.append(observe_identity(Path(expected["path"]), item))
    return inventory


def runtime_identity_observations() -> dict[str, Any]:
    try:
        sources: list[str] | None = sorted(
            path.name for path in Path("/sys/bus/event_source/devices").iterdir()
        )
        sources_error = None
    except OSError as error:
        sources, sources_error = None, str(error)
    return {
        "event_sources": sources, "event_sources_error": sources_error,
        "perf_event_paranoid": (read_optional(Path("/proc/sys/kernel/perf_event_paranoid")) or "").strip(),
        "online_cpus": (read_optional(Path("/sys/devices/system/cpu/online")) or "").strip(),
        "v4_affected_paths_present": [
            relative for relative in ("wall-1t", "wall-4t", "profiles")
            if (V4_ROOT / relative).exists()
        ],
    }


def identity_findings(
    protocol: dict[str, Any], inventory: list[dict[str, Any]], runtime: dict[str, Any],
) -> list[str]:
    ext = protocol["extensions"]["cpu_baseline_aa_v5"]
    findings: list[str] = []
    observed_by_path = {item.get("path"): item for item in inventory}
    for item in ext["required_files"]:
        path = Path(item["path"])
        observed = observed_by_path.get(str(path), {})
        if (
            not observed.get("exists") or observed.get("bytes") != item["bytes"]
            or observed.get("sha256") != item["sha256"]
        ):
            findings.append(f"required identity mismatch: {path}")
            continue
        if item.get("mode") and observed.get("mode") != item["mode"]:
            findings.append(f"required mode mismatch: {path}")
    dependency_observations = [
        item for item in inventory if item.get("scope") == "runtime_dependency"
    ]
    dependency_entries: list[dict[str, Any]] = []
    for observed in dependency_observations:
        entry = {
            field: observed.get(field)
            for field in ("group", "path", "bytes", "mode", "sha256")
        }
        if "link_target" in observed:
            entry["link_target"] = observed.get("link_target")
        dependency_entries.append(entry)
    contract = ext.get("runtime_dependency_manifest", {})
    if (
        len(dependency_entries) != contract.get("file_count")
        or digest_value(dependency_entries) != contract.get("entries_sha256")
        or any(not item.get("exists") for item in dependency_observations)
    ):
        findings.append("runtime dependency inventory differs from the frozen manifest")
    if runtime.get("event_sources_error") is not None:
        findings.append(f"cannot read perf event-source inventory: {runtime['event_sources_error']}")
    elif runtime.get("event_sources") != ["breakpoint", "msr", "software"]:
        findings.append(f"perf event-source inventory changed: {runtime.get('event_sources')}")
    if runtime.get("perf_event_paranoid") != "2":
        findings.append("kernel.perf_event_paranoid changed")
    if runtime.get("online_cpus") != "0-4":
        findings.append("online CPU inventory changed")
    for relative in runtime.get("v4_affected_paths_present", []):
        findings.append(f"v4 acquired affected data after the v5 amendment: {relative}")
    return findings


def audit_identity(protocol: dict[str, Any]) -> list[str]:
    return identity_findings(
        protocol, identity_inventory(protocol), runtime_identity_observations(),
    )


def verify_identity(protocol: dict[str, Any]) -> None:
    findings = audit_identity(protocol)
    if findings:
        raise RuntimeError("; ".join(findings))


def write_identity_snapshot_once(
    label: str, protocol: dict[str, Any], inventory: list[dict[str, Any]] | None = None,
) -> None:
    path = RUN_ROOT / f"orchestration/identity-{label}.json"
    if not path.exists():
        write_json_durable_once(path, {
            "schema": "cpu-baseline-aa-v5-identity-snapshot/v1", "label": label,
            "captured_at": utc_now(),
            "required_files": inventory if inventory is not None else identity_inventory(protocol),
        })


def select_perf_record_from_counts(counts: dict[str, int]) -> list[str]:
    if set(counts) != set(C_IDS) or any(not isinstance(value, int) or value <= 0 for value in counts.values()):
        raise ValueError("selection requires one positive integer Ir count for every C cell")
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
    prelude_error = validate_callgrind_registry_prelude(output, record)
    if prelude_error is not None:
        return None, prelude_error
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
    stdout_path = output / "stdout.txt"
    stderr_path = output / "stderr.txt"
    if (
        not stdout_path.is_file() or not stderr_path.is_file()
        or inner.get("stdout_sha256") != sha256(stdout_path)
        or inner.get("stderr_sha256") != sha256(stderr_path)
    ):
        return None, "inner Callgrind streams are absent or hash-mismatched"
    try:
        stdout_rows = [
            json.loads(line) for line in stdout_path.read_text(encoding="utf-8").splitlines()
            if line.startswith("{")
        ]
    except json.JSONDecodeError as error:
        return None, f"inner Callgrind stdout is malformed: {error}"
    collected = re.findall(r"Collected\s*:\s*(\d+)", stderr_path.read_text(encoding="utf-8"))
    if len(stdout_rows) != 1 or len(collected) != 1:
        return None, "inner Callgrind streams do not contain exactly one row/count"
    expected_row = {**stdout_rows[0], "ir": int(collected[0])}
    if row != expected_row:
        return None, "Callgrind result is not content-bound to captured streams"
    if (
        row.get("id") != record["kernel"]
        or not isinstance(row.get("ir"), int)
        or row["ir"] <= 0
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
    write_json_durable_once(path, {
        "schema": "cpu-baseline-aa-v5-terminal/v1", "status": status,
        "finished_at": utc_now(), "continuation": "forbidden", **fields,
    })


def seal_finalization_failure(reason: str, **fields: Any) -> None:
    path = RUN_ROOT / "orchestration/finalization-failure.json"
    if path.exists():
        return
    write_json_durable_once(path, {
        "schema": "cpu-baseline-aa-v5-finalization-failure/v1",
        "status": "derived_finalization_incomplete", "reason": reason,
        "finished_at": utc_now(),
        "measurement_continuation": "forbidden",
        "analysis_only_retry": "allowed_until_validated_finalization_exists",
        **fields,
    })


def validate_finalization(
    protocol_path: Path, expected_returncode: int | None, require_terminal: bool,
) -> tuple[bool, str]:
    export_path = RUN_ROOT / "export.json"
    finalization_path = RUN_ROOT / "orchestration/finalization.json"
    if not export_path.is_file() or not finalization_path.is_file():
        return False, "export or validated finalization receipt is absent"
    try:
        export = json.loads(export_path.read_text(encoding="utf-8"))
        finalization = json.loads(finalization_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return False, f"malformed export/finalization receipt: {error}"
    derived_returncode, derivation_error = derive_scientific_returncode()
    if derivation_error is not None:
        return False, derivation_error
    receipt_returncode = finalization.get("scientific_returncode")
    if (
        finalization.get("schema") != "cpu-baseline-aa-v5-finalization/v1"
        or finalization.get("status") != "validated"
        or finalization.get("export_sha256") != sha256(export_path)
        or finalization.get("analyzer_sha256") != sha256(ANALYZER)
        or not isinstance(receipt_returncode, int)
        or isinstance(receipt_returncode, bool)
        or parse_utc(finalization.get("completed_at")) is None
        or receipt_returncode != derived_returncode
    ):
        return False, "validated finalization receipt does not causally bind the export/analyzer/outcome"
    if expected_returncode is not None and receipt_returncode != expected_returncode:
        return False, "analyzer process and scientific return codes differ"
    if require_terminal:
        terminal_path = RUN_ROOT / "orchestration/terminal.json"
        terminal_entries = [
            item for item in export.get("files", [])
            if item.get("path") == "orchestration/terminal.json"
        ]
        if (
            not terminal_path.is_file() or len(terminal_entries) != 1
            or terminal_entries[0].get("sha256") != sha256(terminal_path)
        ):
            return False, "terminal outcome is absent or stale in the canonical export inventory"
    checked = subprocess.run(
        closed_python_command(
            PROTOCOL_TOOL, "check-export", "--protocol", str(protocol_path),
            "--verify-files", str(export_path),
        ),
        cwd=RUN_ROOT, capture_output=True, text=True, timeout=60,
    )
    if checked.returncode != 0:
        return False, f"independent canonical check-export failed: {checked.stderr[-1000:]}"
    return True, "validated"


def derive_scientific_returncode() -> tuple[int | None, str | None]:
    """Derive the analyzer's scientific code from immutable retained state."""
    analysis_path = RUN_ROOT / "analysis/analysis.json"
    complete_path = RUN_ROOT / "orchestration/complete.json"
    terminal_path = RUN_ROOT / "orchestration/terminal.json"
    try:
        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, f"analysis needed to derive scientific return code is malformed: {error}"
    if analysis.get("schema") != "cpu-baseline-aa-v5-analysis/v1":
        return None, "analysis schema cannot derive the scientific return code"
    if complete_path.is_file() == terminal_path.is_file():
        return None, "exactly one completion or terminal receipt is required"
    if complete_path.is_file():
        try:
            complete = json.loads(complete_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            return None, f"completion receipt is malformed: {error}"
        if (
            set(complete) != {"schema", "status", "finished_at"}
            or complete.get("schema") != "cpu-baseline-aa-v5-complete/v1"
            or complete.get("status") != "orchestration_complete"
            or parse_utc(complete.get("finished_at")) is None
            or analysis.get("campaign_status") != "orchestration_complete"
            or analysis.get("terminal") is not None
            or analysis.get("wall", {}).get("verdict") not in {
                "baseline_aa_complete_nonqualified",
                "baseline_aa_false_direction_nonqualified",
            }
            or analysis.get("verdict") != analysis.get("wall", {}).get("verdict")
        ):
            return None, "completion/analysis state cannot derive a successful scientific outcome"
        return 0, None
    try:
        terminal = json.loads(terminal_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, f"terminal receipt is malformed: {error}"
    if (
        terminal.get("schema") != "cpu-baseline-aa-v5-terminal/v1"
        or terminal.get("continuation") != "forbidden"
        or parse_utc(terminal.get("finished_at")) is None
        or analysis.get("campaign_status") != "sealed_terminal_incomplete"
        or analysis.get("terminal") != terminal
    ):
        return None, "terminal/analysis state cannot derive an incomplete scientific outcome"
    return 1, None


def emit_terminal_analysis(protocol_path: Path) -> bool:
    """Finalize a terminal run, or seal an explicit unexportable outcome."""
    try:
        protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
        write_identity_snapshot_once("wall-after", protocol)
        write_system_snapshot_once("wall-after")
        write_identity_snapshot_once("campaign-after", protocol)
        write_system_snapshot_once("campaign-after")
        completed = subprocess.run(
            closed_python_command(
                ANALYZER, "--protocol", str(protocol_path),
                "--run-root", str(RUN_ROOT),
            ),
            cwd=REPO, timeout=ATTEMPT_TIMEOUT_SECONDS,
        )
        if completed.returncode not in (0, 1):
            raise RuntimeError(f"analyzer exited {completed.returncode}")
        valid, reason = validate_finalization(
            protocol_path, completed.returncode, require_terminal=True,
        )
        if not valid:
            raise RuntimeError(reason)
        return True
    except BaseException as error:
        seal_finalization_failure(
            "terminal_analysis_failed", error_type=type(error).__name__, error=str(error),
        )
        return False


def initialize_campaign(protocol_path: Path, protocol: dict[str, Any]) -> bool:
    orchestration = RUN_ROOT / "orchestration"
    plan = build_plan()
    if CLOSED_BOOTSTRAP_ENTRY is None:
        raise RuntimeError("campaign start lacks the frozen controller bootstrap-entry proof")
    write_json_durable_once(orchestration / "command-plan.json", plan)
    write_json_durable_once(orchestration / "start.json", {
        "schema": "cpu-baseline-aa-v5-start/v1", "started_at": utc_now(),
        "protocol_path": str(protocol_path),
        "protocol_sha256": protocol["freeze"]["protocol_sha256"],
        "plan_sha256": sha256(orchestration / "command-plan.json"),
        "plan_preimage_sha256": plan["digests"]["plan_preimage"],
        "controller_entry": CLOSED_BOOTSTRAP_ENTRY,
        "other_cpu_work_paused_confirmed": True, "resume_policy": "forbidden",
    })
    write_system_snapshot_once("before")
    before_inventory = identity_inventory(protocol)
    runtime_observations = runtime_identity_observations()
    write_identity_snapshot_once("before", protocol, before_inventory)
    findings = identity_findings(protocol, before_inventory, runtime_observations)
    write_json_durable_once(orchestration / "preflight.json", {
        "schema": "cpu-baseline-aa-v5-preflight/v1", "checked_at": utc_now(),
        "status": "passed" if not findings else "blocked_identity_mismatch",
        "findings": findings, "required_files": before_inventory,
        "runtime_observations": runtime_observations,
    })
    if findings:
        write_terminal_once("preflight_identity_blocked", findings=findings)
        emit_terminal_analysis(protocol_path)
        return False
    processes = subprocess.check_output(
        [str(PS), "-eLo", "pid,ppid,lwp,psr,stat,etime,pcpu,pmem,comm"],
        text=True, timeout=60,
    )
    write_text_durable_once(orchestration / "processes-before.txt", processes)
    return True


def execute_campaign(protocol_path: Path, protocol: dict[str, Any]) -> int:
    orchestration = RUN_ROOT / "orchestration"
    plan = build_plan()

    for index, record in enumerate(plan["wall"], 1):
        if run_attempt(record, orchestration / f"attempts/wall-{index:02d}-{record['id']}") != 0:
            write_terminal_once("wall_command_failed", record=record)
            emit_terminal_analysis(protocol_path)
            return 1
    write_identity_snapshot_once("wall-after", protocol)
    write_system_snapshot_once("wall-after")
    gate = subprocess.run(
        closed_python_command(
            ANALYZER, "--protocol", str(protocol_path),
            "--run-root", str(RUN_ROOT), "--wall-gate-only",
        ),
        cwd=REPO, timeout=ATTEMPT_TIMEOUT_SECONDS,
    )
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

    write_identity_snapshot_once("campaign-after", protocol)
    write_system_snapshot_once("campaign-after")
    write_json_once(orchestration / "complete.json", {
        "schema": "cpu-baseline-aa-v5-complete/v1",
        "status": "orchestration_complete", "finished_at": utc_now(),
    })
    write_json_once(orchestration / "finalization-request.json", {
        "schema": "cpu-baseline-aa-v5-finalization-request/v1",
        "status": "analysis_started", "started_at": utc_now(),
    })
    analysis = subprocess.run(
        closed_python_command(
            ANALYZER, "--protocol", str(protocol_path),
            "--run-root", str(RUN_ROOT),
        ),
        cwd=REPO, timeout=ATTEMPT_TIMEOUT_SECONDS,
    )
    valid, reason = validate_finalization(
        protocol_path, analysis.returncode, require_terminal=False,
    )
    if not valid:
        seal_finalization_failure(
            "analysis_or_export_failed", returncode=analysis.returncode,
            validation_error=None if valid else reason,
        )
        return 2
    return analysis.returncode


def command_run(options: argparse.Namespace) -> int:
    protocol_path = options.protocol.resolve()
    if not options.confirm_other_cpu_work_paused:
        raise SystemExit("run requires --confirm-other-cpu-work-paused")
    protocol = validate_protocol(protocol_path)
    if RUN_ROOT.exists():
        raise SystemExit(f"refusing existing one-shot run root: {RUN_ROOT}")
    RUN_ROOT.mkdir(parents=True, mode=0o700)
    (RUN_ROOT / "orchestration").mkdir(mode=0o700)
    try:
        if not initialize_campaign(protocol_path, protocol):
            return 1
        return execute_campaign(protocol_path, protocol)
    except KeyboardInterrupt:
        if (RUN_ROOT / "orchestration/complete.json").is_file():
            seal_finalization_failure(
                "analysis_interrupted_after_completed_measurement",
                error_type="KeyboardInterrupt", error="KeyboardInterrupt",
            )
            return 130
        write_terminal_once("interrupted_by_operator", error="KeyboardInterrupt")
        if protocol is not None and (RUN_ROOT / "orchestration/start.json").is_file():
            emit_terminal_analysis(protocol_path)
        else:
            seal_finalization_failure("interrupted_before_validated_protocol_or_start")
        return 130
    except Exception as error:  # the sealed root is evidence; never resume it
        if (RUN_ROOT / "orchestration/complete.json").is_file():
            seal_finalization_failure(
                "analysis_exception_after_completed_measurement",
                error_type=type(error).__name__, error=str(error),
            )
            print(
                f"cpu baseline A/A v5 analysis terminated after measurement completion: "
                f"{type(error).__name__}: {error}", file=sys.stderr,
            )
            return 2
        write_terminal_once(
            "orchestration_exception", error_type=type(error).__name__, error=str(error),
        )
        if protocol is not None and (RUN_ROOT / "orchestration/start.json").is_file():
            emit_terminal_analysis(protocol_path)
        else:
            seal_finalization_failure(
                "exception_before_validated_protocol_or_start",
                error_type=type(error).__name__, error=str(error),
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
    matching_records = [
        record for record in callgrind_commands()
        if record["kernel"] == options.kernel and Path(record["output"]) == output
    ]
    if len(matching_records) != 1:
        raise SystemExit("Callgrind output is outside the frozen attempt plan")
    record = matching_records[0]
    output.mkdir(parents=True)
    if callgrind_requires_registry_prelude(record):
        language = "rust" if options.kernel in RUST_IDS else "c"
        expected_rows = [
            json.loads(line)
            for line in (V4_ROOT / f"registry/{language}.jsonl").read_text().splitlines()
            if line.strip()
        ]
        if language == "rust":
            expected_rows = [row for row in expected_rows if row.get("tier") == "Quick"]
        selected, prelude_status = run_registry_prelude(
            output, {"binary": options.binary, "language": language}, expected_rows,
        )
        if selected is None:
            write_text_once(output / "status.txt", f"{prelude_status}\n")
            return prelude_status
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
        "stdout_sha256": sha256(output / "stdout.txt"),
        "stderr_sha256": sha256(output / "stderr.txt"),
    }
    if proc.returncode == 0:
        try:
            rows = [json.loads(line) for line in proc.stdout.splitlines() if line.startswith("{")]
        except json.JSONDecodeError:
            rows = []
        match = re.search(r"Collected\s*:\s*(\d+)", proc.stderr)
        if (
            len(rows) != 1 or match is None
            or rows[0].get("id") != options.kernel
            or not isinstance(rows[0].get("fingerprint"), str)
            or not rows[0].get("fingerprint")
        ):
            receipt["parse_error"] = "expected one JSON row and one Callgrind Collected count"
            receipt["effective_returncode"] = 2
        else:
            row = rows[0]
            row["ir"] = int(match.group(1))
            write_json_once(output / "result.json", row)
    write_text_once(output / "status.txt", f"{receipt['effective_returncode']}\n")
    write_json_once(output / "receipt.json", receipt)
    return receipt["effective_returncode"]


def is_campaign_cmdline(command: bytes) -> bool:
    needles = (
        str(RUNNER).encode(), str(ANALYZER).encode(), str(RUN_ROOT).encode(),
        b"cpu-baseline-aa-v5-", str(RUST_BINARY).encode(), str(C_BINARY).encode(),
    )
    return any(needle in command for needle in needles)


def live_campaign_processes() -> list[int]:
    result: list[int] = []
    for directory in Path("/proc").iterdir():
        if not directory.name.isdigit() or int(directory.name) == os.getpid():
            continue
        try:
            command = (directory / "cmdline").read_bytes()
        except OSError:
            continue
        if is_campaign_cmdline(command):
            result.append(int(directory.name))
    return sorted(result)


def command_finalize(options: argparse.Namespace) -> int:
    """Analyze a stopped one-shot root; never launch a benchmark/profiler."""
    protocol_path = options.protocol.resolve()
    validate_protocol(protocol_path)
    if not options.confirm_no_campaign_process_live:
        raise SystemExit("finalize requires --confirm-no-campaign-process-live")
    if not RUN_ROOT.is_dir():
        raise SystemExit(f"cannot finalize absent run root: {RUN_ROOT}")
    live = live_campaign_processes()
    if live:
        raise SystemExit(f"refusing finalize while campaign/analyzer processes are live: {live}")
    finalization_path = RUN_ROOT / "orchestration/finalization.json"
    if finalization_path.is_file():
        valid, reason = validate_finalization(
            protocol_path, None,
            require_terminal=(RUN_ROOT / "orchestration/terminal.json").is_file(),
        )
        if not valid:
            raise SystemExit(f"existing finalization is invalid: {reason}")
        derived, error = derive_scientific_returncode()
        if error is not None or derived is None:
            raise SystemExit(f"cannot derive existing finalization outcome: {error}")
        return derived
    complete = RUN_ROOT / "orchestration/complete.json"
    terminal = RUN_ROOT / "orchestration/terminal.json"
    if not complete.is_file() and not terminal.is_file():
        write_terminal_once(
            "orphaned_after_process_loss",
            reason="no live campaign process and no completion receipt",
        )
    if terminal.is_file():
        return 1 if emit_terminal_analysis(protocol_path) else 2
    completed = subprocess.run(
        closed_python_command(
            ANALYZER, "--protocol", str(protocol_path),
            "--run-root", str(RUN_ROOT),
        ),
        cwd=REPO, timeout=ATTEMPT_TIMEOUT_SECONDS,
    )
    valid, reason = validate_finalization(
        protocol_path, completed.returncode, require_terminal=False,
    )
    if not valid:
        seal_finalization_failure(
            "crash_recovery_analysis_failed", returncode=completed.returncode,
            validation_error=reason,
        )
        return 2
    return completed.returncode


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
    finalize = sub.add_parser("finalize")
    finalize.add_argument("--protocol", type=Path, required=True)
    finalize.add_argument("--confirm-no-campaign-process-live", action="store_true")
    finalize.set_defaults(func=command_finalize)
    wall = sub.add_parser("wall-session")
    wall.add_argument("--session", choices=tuple(WALL_SESSION_SPECS), required=True)
    wall.add_argument("--out", type=Path, required=True)
    wall.set_defaults(func=command_wall_session)
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
    if parsed.command == "wall-session":
        expected_profile = f"wall-{WALL_SESSION_SPECS[parsed.session]['threads']}"
    elif parsed.command == "callgrind-one":
        expected_profile = "callgrind-1"
    else:
        expected_profile = "base"
    require_closed_bootstrap(expected_profile)
    raise SystemExit(parsed.func(parsed))
