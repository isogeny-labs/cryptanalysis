#!/usr/bin/env python3
"""Seal and run a two-way N83 root-index capacity comparison."""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "adaptive_all_orientations_20261004"
INPUTS = PARENT / "inputs"
CRYPTO = Path(os.environ.get("N83_CRYPTO_ROOT", "/Volumes/SSD990/crypto"))
TARGET_DIR = Path(os.environ.get("N83_TARGET_DIR", "/Volumes/SSD990-2/tmp/n83-tier1-target"))
MODES = ("hash", "split-hash", "split-hash", "hash")
PROPOSAL_ID = "Q2026101906"
STATE_CAP = 4_000_000
MEMORY_CAP_MIB = 1024
CRYPTO_COMMIT = "46416a4129c299dad4b1fd62d1a620dbd0d34317"
RUNPOD_POD_ID = "thyvmdqmzsz5ik"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def save(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, sort_keys=True, indent=2) + "\n")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def rust_source_tree_digest() -> str:
    h = hashlib.sha256()
    for path in sorted((CRYPTO / "src").rglob("*.rs")):
        h.update(str(path.relative_to(CRYPTO)).encode())
        h.update(b"\0")
        h.update(bytes.fromhex(digest(path)))
    return h.hexdigest()


def prepare() -> tuple[dict, dict]:
    require(subprocess.check_output(["git", "-C", str(CRYPTO), "rev-parse", "HEAD"],
                                    text=True).strip() == CRYPTO_COMMIT,
            "crypto source commit differs from the Tier 1 pin")
    parent_path = PARENT / "all83_ordinary_manifest.json"
    parent = json.loads(parent_path.read_text())
    reps = INPUTS / "n83_x_representatives.bin"
    bridge = INPUTS / "n83_onb_poly_bridge.json"
    assert digest(reps) == parent["representatives_file_sha256"]
    assert digest(bridge) == parent["bridge_sha256"]
    assert parent["curve_id"] == json.loads(bridge.read_text())["curve_id"]
    assert parent["candidate_id"] is None and parent["run_id"] is None
    assert parent["target_count"] == 1 and parent["field_degree"] == 83
    assert parent["pair_state_cap"] == 2_000_000
    assert parent["peak_rss_cap_mib"] == MEMORY_CAP_MIB

    total = parent["representative_count_K"] ** 2 * 83
    origin = 0x7E5218AC20261003 % total
    step = 0x9E3779B97F4A7C15 % total or 1
    while math.gcd(step, total) != 1:
        step += 1
    workload = {
        "curve_id": parent["curve_id"],
        "subgroup_order": str(parent["subgroup_order"]),
        "target_count": 1,
        "target_poly_xy": parent["target_poly_xy"],
        "target_input_law": "one frozen public subgroup point",
        "factor_base_enumerated_set_sha256": parent["factor_base_enumerated_set_sha256"],
        "representatives_file_sha256": digest(reps),
        "index_state_law": {
            "kind": "coprime_stride_without_replacement",
            "total": total, "count": STATE_CAP,
            "origin": origin, "step": step,
        },
        "target_orientations_per_state": 1,
        "cache_state": "target-independent base and index ready at target clock start",
    }
    workload_id = hashlib.sha256(canonical(workload)).hexdigest()[:12]
    save(HERE / "workload.json", workload)

    source = HERE / "native_packed_index.rs"
    cargo_manifest = HERE / "Cargo.toml"
    cargo_lock = HERE / "Cargo.lock"
    protocol = {
        "kind": "paired_n83_packed_root_index_runpod_tier1_protocol",
        "proposal_id": PROPOSAL_ID,
        "candidate_id": None,
        "run_id": None,
        "curve_id": parent["curve_id"],
        "workload_id": workload_id,
        "claim_boundary": "Tier 1 RunPod CPU Pod replay of bounded four-million-state index capacity; cap failures remain measured outcomes, with no complete factor-base or online speedup selection",
        "comparison_variable": "root-index storage: separate key/value open addressing versus one exact 16-byte split-u64 slot at four million sampled pair states",
        "runpod": {"pod_id": RUNPOD_POD_ID, "tier": "Tier 1 cloud Pod",
                   "declared_vcpu": 8, "declared_memory_gib": 16,
                   "declared_gpu": 0, "api_cost_per_hour_usd": "0.24",
                   "max_active_seconds": 5400, "estimated_compute_cap_usd": "0.36",
                   "stop_rule": "stop the Pod immediately after receipts or on any operational failure"},
        "crypto_commit": CRYPTO_COMMIT,
        "run_order": list(MODES),
        "limits": {"pair_state_cap": STATE_CAP,
                   "peak_rss_cap_mib": MEMORY_CAP_MIB,
                   "memory_gate": "worker_samples_process_peak_RSS_after_each_4096_state_window",
                   "hard_os_memory_limit": None,
                   "target_orientations_per_state": 1,
                   "index_s3_window_size": 4096,
                   "target_s3_window_schedule": [4096]},
        "inputs_sha256": {
            "parent_manifest": digest(parent_path),
            "bridge": digest(bridge),
            "representatives": digest(reps),
            "native_source": digest(source),
            "runner": digest(HERE / "run.py"),
            "cargo_manifest": digest(cargo_manifest),
            "cargo_lock": digest(cargo_lock),
            "crypto_rust_source_tree": rust_source_tree_digest(),
        },
        "accounting": {
            "index_build": "target-independent S3 roots, insertion, packed sort, and prefix-directory construction",
            "target_query": "target-dependent S3 probes and relation checks",
            "correctness": "first-witness lookup samples and same-point arithmetic replay; preserve each arm's index-state count and capped status",
            "cpu_timing_boundary": "Tier 1 cloud Pod; stage-only paired timings with exposed cgroup and calibration envelope, hash target stage censored if its index build reaches the memory gate",
        },
    }
    save(HERE / "protocol.json", protocol)
    manifest = {
        "kind": "paired_n83_packed_root_index_stage_input",
        "stage_id": "n83_packed_index_e1_runpod_tier1_20261019",
        "stage_protocol_sha256": digest(HERE / "protocol.json"),
        "proposal_id": PROPOSAL_ID,
        "parent_factor_base_proposal_id": parent["parent_factor_base_proposal_id"],
        "candidate_id": None,
        "run_id": None,
        "curve_id": parent["curve_id"],
        "workload_id": workload_id,
        "field_degree": 83,
        "polynomial_low_terms": parent["polynomial_low_terms"],
        "subgroup_order": parent["subgroup_order"],
        "target_count": 1,
        "target_poly_xy": parent["target_poly_xy"],
        "representative_count_K": parent["representative_count_K"],
        "representatives_file_sha256": digest(reps),
        "factor_base_enumerated_set_sha256": parent["factor_base_enumerated_set_sha256"],
        "actual_usable_points_B": parent["actual_usable_points_B"],
        "pair_state_cap": STATE_CAP,
        "peak_rss_cap_mib": MEMORY_CAP_MIB,
        "orientations_per_state": 1,
        "index_s3_window_size": 4096,
        "target_s3_window_schedule": [4096],
    }
    save(HERE / "stage_manifest.json", manifest)
    return protocol, manifest


def build(protocol: dict) -> Path:
    env = os.environ.copy()
    env.update({
        "NATIVE_S3_SOURCE_SHA256": protocol["inputs_sha256"]["native_source"],
        "NATIVE_S3_BUILD_MANIFEST_SHA256": protocol["inputs_sha256"]["cargo_manifest"],
        "CARGO_TARGET_DIR": str(TARGET_DIR),
    })
    command = ["cargo", "build", "--release", "--locked", "--manifest-path",
               str(HERE / "Cargo.toml")]
    result = subprocess.run(command, env=env, text=True, capture_output=True)
    (HERE / "build.stdout.txt").write_text(result.stdout)
    (HERE / "build.stderr.txt").write_text(result.stderr)
    if result.returncode:
        raise RuntimeError(f"cargo build failed with exit code {result.returncode}")
    return TARGET_DIR / "release" / "native_packed_index"


def system_text(path: str) -> str | None:
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def host_probe() -> dict:
    stat = system_text("/sys/fs/cgroup/cpu.stat")
    cpu_stat = {parts[0]: int(parts[1]) for line in (stat or "").splitlines()
                if len(parts := line.split()) == 2 and parts[1].isdigit()}
    proc_stat = system_text("/proc/stat")
    cpu_line = (proc_stat or "").splitlines()[0].split() if proc_stat else []
    return {
        "affinity_cpus": sorted(os.sched_getaffinity(0))
            if hasattr(os, "sched_getaffinity") else None,
        "logical_cpus_visible": os.cpu_count(),
        "cpu_max": system_text("/sys/fs/cgroup/cpu.max"),
        "cpuset_effective": system_text("/sys/fs/cgroup/cpuset.cpus.effective"),
        "memory_max": system_text("/sys/fs/cgroup/memory.max"),
        "cpu_stat": cpu_stat,
        "host_steal_jiffies": int(cpu_line[8]) if len(cpu_line) > 8 else None,
        "cpu0_frequency_khz": system_text(
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"),
    }


def calibration_ns() -> int:
    start = time.perf_counter_ns()
    value = 0x9e3779b97f4a7c15
    for _ in range(1_000_000):
        value = ((value ^ (value >> 13)) * 0xbf58476d1ce4e5b9) & ((1 << 64) - 1)
    assert value != 0
    return time.perf_counter_ns() - start


def counter_delta(before: dict, after: dict, field: str) -> int | None:
    left = before["cpu_stat"].get(field)
    right = after["cpu_stat"].get(field)
    return right - left if left is not None and right is not None else None


def host_record(binary: Path, protocol: dict) -> dict:
    cpu = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                         text=True, capture_output=True) if shutil.which("sysctl") else None
    cpuinfo = system_text("/proc/cpuinfo")
    model = next((line.split(":", 1)[1].strip() for line in
                  (cpuinfo or "").splitlines() if line.startswith("model name")), None)
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": model or (cpu.stdout.strip() if cpu and cpu.returncode == 0
                               else platform.processor()),
        "python": sys.version.split()[0],
        "rustc": subprocess.check_output(["rustc", "--version"], text=True).strip(),
        "cargo": subprocess.check_output(["cargo", "--version"], text=True).strip(),
        "binary_sha256": digest(binary),
        "rust_temporary_directory": os.environ.get("TMPDIR"),
        "protocol_sha256": digest(HERE / "protocol.json"),
        "stage_manifest_sha256": digest(HERE / "stage_manifest.json"),
        "workload_sha256": digest(HERE / "workload.json"),
        "source_sha256": protocol["inputs_sha256"]["native_source"],
        "runpod_pod_id": os.environ.get("RUNPOD_POD_ID"),
        "topology_and_cgroup_before_panel": host_probe(),
        "host_isolation_receipt": None,
    }


def run_one(binary: Path, mode: str, number: int, host: dict) -> dict:
    stem = f"run_{number}_{mode}"
    raw = HERE / f"{stem}.json"
    if raw.exists() or (HERE / f"{stem}.record.json").exists():
        raise FileExistsError(f"first-attempt output already exists: {stem}")
    command = [str(binary), str(HERE / "stage_manifest.json"),
               str(INPUTS / "n83_onb_poly_bridge.json"),
               str(INPUTS / "n83_x_representatives.bin"),
               str(STATE_CAP), str(MEMORY_CAP_MIB), mode, str(raw)]
    before = host_probe()
    calibration_before_ns = calibration_ns()
    try:
        completed = subprocess.run(command, text=True, capture_output=True,
                                   timeout=180)
        status = "completed" if completed.returncode == 0 else "failed"
        code = completed.returncode
        out, err = completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as exc:
        status, code = "timeout", None
        out = exc.stdout.decode(errors="replace") if exc.stdout else ""
        err = exc.stderr.decode(errors="replace") if exc.stderr else ""
    calibration_after_ns = calibration_ns()
    after = host_probe()
    (HERE / f"{stem}.stdout.txt").write_text(out)
    (HERE / f"{stem}.stderr.txt").write_text(err)
    result = {
        "kind": "n83_packed_index_stage_run_record",
        "proposal_id": PROPOSAL_ID,
        "candidate_id": None,
        "run_id": None,
        "mode": mode,
        "sequence_number": number,
        "execution_status": status,
        "exit_code": code,
        "raw_result_sha256": digest(raw) if raw.exists() else None,
        "tier1_envelope": {
            "before": before, "after": after,
            "cgroup_nr_throttled_delta": counter_delta(before, after, "nr_throttled"),
            "cgroup_throttled_usec_delta": counter_delta(before, after, "throttled_usec"),
            "host_steal_jiffies_delta":
                after["host_steal_jiffies"] - before["host_steal_jiffies"]
                if before["host_steal_jiffies"] is not None and
                   after["host_steal_jiffies"] is not None else None,
            "calibration_before_ns": calibration_before_ns,
            "calibration_after_ns": calibration_after_ns,
            "calibration_ratio": max(calibration_before_ns, calibration_after_ns) /
                                 min(calibration_before_ns, calibration_after_ns),
        },
        "host": host,
    }
    save(HERE / f"{stem}.record.json", result)
    return result


def summarize(records: list[dict], protocol: dict, manifest: dict) -> dict:
    raw = [json.loads((HERE / f"run_{i}_{mode}.json").read_text())
           for i, mode in enumerate(MODES, 1)]
    expected = raw[0]
    invariants = ["curve_id", "workload_id", "factor_base_enumerated_set_sha256",
                  "lookup_sample", "native_s3_generator_target_control"]
    mismatches = {field: [item[field] for item in raw]
                  for field in invariants if any(item[field] != expected[field]
                                                 for item in raw[1:])}
    repeat_fields = ["status", "index_pair_states_examined",
                     "index_satisfiable_s3_states", "index_distinct_root_keys",
                     "target_states_scanned", "relation", "operation_counts"]
    repeat_variation = {mode: {
        field: [item[field] for item in raw if item["index_mode"] == mode]
        for field in repeat_fields if len({json.dumps(item[field], sort_keys=True)
            for item in raw if item["index_mode"] == mode}) > 1
    } for mode in dict.fromkeys(MODES)}
    rows = []
    for record, item in zip(records, raw):
        rows.append({
            "sequence_number": record["sequence_number"],
            "mode": record["mode"],
            "status": item["status"],
            "index_pair_states_examined": item["index_pair_states_examined"],
            "index_satisfiable_s3_states": item["index_satisfiable_s3_states"],
            "target_states_scanned": item["target_states_scanned"],
            "index_build_ns": int(item["timing_ns"]["index_build"]),
            "target_stage_ns": int(item["timing_ns"]["target_pdp_and_native_check"]),
            "rss_after_index_bytes": item["rss_after_index_bytes"],
            "peak_rss_bytes": item["peak_rss_bytes"],
            "table_allocated_bytes": item["root_table_allocated_bytes"],
            "table_slots_or_records": item["root_table_slots_or_records"],
            "target_lookup_comparisons_or_probes": item["root_table_hash_probes"]["target_lookup"],
            "verified_relation": item["relation"] is not None,
        })
    medians = {mode: {
        field: statistics.median(row[field] for row in rows if row["mode"] == mode)
        for field in ("index_build_ns", "target_stage_ns", "rss_after_index_bytes",
                      "peak_rss_bytes", "table_allocated_bytes")
    } for mode in dict.fromkeys(MODES)}
    ranges = {mode: {
        field: [min(row[field] for row in rows if row["mode"] == mode),
                max(row[field] for row in rows if row["mode"] == mode)]
        for field in ("index_build_ns", "target_stage_ns", "peak_rss_bytes")
    } for mode in dict.fromkeys(MODES)}
    return {
        "kind": "n83_packed_root_index_capacity_comparison",
        "proposal_id": PROPOSAL_ID,
        "candidate_id": None, "run_id": None,
        "curve_id": manifest["curve_id"],
        "workload_id": manifest["workload_id"],
        "status": "validated_bounded_capacity_screen" if not mismatches else "mismatch",
        "invariant_mismatches": mismatches,
        "within_mode_variation": repeat_variation,
        "protocol_sha256": digest(HERE / "protocol.json"),
        "source_sha256": protocol["inputs_sha256"]["native_source"],
        "paired_rows": rows,
        "medians": medians,
        "ranges": ranges,
        "index_satisfiable_states_by_mode": {mode: [item["index_satisfiable_s3_states"]
            for item in raw if item["index_mode"] == mode] for mode in dict.fromkeys(MODES)},
        "distinct_root_keys_by_mode": {mode: [item["index_distinct_root_keys"]
            for item in raw if item["index_mode"] == mode] for mode in dict.fromkeys(MODES)},
        "actual_usable_points_B": expected["actual_usable_points_B"],
        "folded_columns_K": expected["folded_columns_K"],
        "complete_target_dlp": False,
        "rho_online_ms": None,
        "ic_online_ms": None,
        "online_speedup": None,
        "cpu_timing_claim": "Tier 1 stage costs only; inspect per-call cgroup and calibration receipts before comparing completed arms",
    }


def load_seal() -> tuple[dict, dict]:
    protocol_path = HERE / "protocol.json"
    manifest_path = HERE / "stage_manifest.json"
    protocol = json.loads(protocol_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    require(protocol["proposal_id"] == PROPOSAL_ID and
            protocol["run_order"] == list(MODES) and
            protocol["crypto_commit"] == CRYPTO_COMMIT and
            protocol["runpod"]["pod_id"] == RUNPOD_POD_ID and
            protocol["limits"]["pair_state_cap"] == STATE_CAP and
            protocol["limits"]["peak_rss_cap_mib"] == MEMORY_CAP_MIB and
            manifest["stage_protocol_sha256"] == digest(protocol_path),
            "protocol or stage manifest differs from the sealed configuration")
    require(subprocess.check_output(["git", "-C", str(CRYPTO), "rev-parse", "HEAD"],
                                    text=True).strip() == CRYPTO_COMMIT,
            "crypto source commit differs from the sealed Tier 1 pin")
    actual_pod = os.environ.get("RUNPOD_POD_ID")
    require(actual_pod is None or actual_pod == RUNPOD_POD_ID,
            "executing on a different RunPod Pod")
    paths = {
        "parent_manifest": PARENT / "all83_ordinary_manifest.json",
        "bridge": INPUTS / "n83_onb_poly_bridge.json",
        "representatives": INPUTS / "n83_x_representatives.bin",
        "native_source": HERE / "native_packed_index.rs",
        "runner": HERE / "run.py",
        "cargo_manifest": HERE / "Cargo.toml",
        "cargo_lock": HERE / "Cargo.lock",
    }
    for label, path in paths.items():
        require(digest(path) == protocol["inputs_sha256"][label],
                f"sealed {label} differs")
    require(rust_source_tree_digest() ==
            protocol["inputs_sha256"]["crypto_rust_source_tree"],
            "crypto source tree differs")
    require(manifest["representatives_file_sha256"] ==
            protocol["inputs_sha256"]["representatives"],
            "manifest representative digest differs")
    return protocol, manifest


def main() -> None:
    if sys.argv[1:] == ["--prepare"]:
        if any((HERE / name).exists() for name in
               ("protocol.json", "stage_manifest.json", "workload.json")):
            raise FileExistsError("sealed input already exists")
        protocol, manifest = prepare()
        print(json.dumps({"status": "PREPARED_FOR_COMMIT",
                          "protocol_sha256": digest(HERE / "protocol.json"),
                          "source_sha256": protocol["inputs_sha256"]["native_source"]},
                         sort_keys=True))
        return
    if sys.argv[1:] != ["--run"]:
        raise SystemExit("usage: run.py --prepare | --run")
    protocol, manifest = load_seal()
    binary = build(protocol)
    host = host_record(binary, protocol)
    save(HERE / "build_receipt.json", host)
    records = []
    for i, mode in enumerate(MODES, 1):
        print(f"run {i}/{len(MODES)} {mode}", flush=True)
        records.append(run_one(binary, mode, i, host))
    if any(record["execution_status"] != "completed" for record in records):
        raise RuntimeError("one or more stage executions failed; raw rows were preserved")
    summary = summarize(records, protocol, manifest)
    save(HERE / "summary.json", summary)
    if summary["invariant_mismatches"]:
        raise RuntimeError("hash and packed results differed; inspect summary.json")
    print(json.dumps({"status": summary["status"],
                      "medians": summary["medians"]}, sort_keys=True))


if __name__ == "__main__":
    main()
