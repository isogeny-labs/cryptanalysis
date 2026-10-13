#!/usr/bin/env python3
"""One-worker public-point derivation plus all right-block native scans."""

import hashlib
import json
import os
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil


HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SAGE = HERE.parents[2] / "sage"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def run_one(command, prefix, deadline_ns, rss_cap):
    stdout_path = prefix.with_suffix(".stdout.txt")
    stderr_path = prefix.with_suffix(".stderr.txt")
    assert not stdout_path.exists() and not stderr_path.exists()
    parent = psutil.Process(os.getpid())
    began = time.monotonic_ns()
    peak_rss = peak_cpu = 0
    monitor_degraded = False
    stop_reason = None
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr,
                                   start_new_session=True)
        child = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                rss = parent.memory_info().rss + child.memory_info().rss
                usage = child.cpu_times()
                peak_cpu = max(peak_cpu, usage.user+usage.system)
                peak_rss = max(peak_rss, rss)
            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                monitor_degraded = True
            if peak_rss > rss_cap:
                stop_reason = "RSS_CAP"
            elif time.monotonic_ns() >= deadline_ns:
                stop_reason = "TOTAL_WALL_CAP"
            if stop_reason:
                os.killpg(process.pid, signal.SIGTERM)
                break
            time.sleep(.1)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            stop_reason = (stop_reason or "DRAIN_TIMEOUT") + "_KILLED"
    ended = time.monotonic_ns()
    return {
        "command": command, "exit_code": process.returncode,
        "stop_reason": stop_reason, "wall_ns": ended-began,
        "sampled_peak_combined_rss_bytes": peak_rss,
        "sampled_peak_child_cpu_seconds": peak_cpu,
        "monitor_degraded": monitor_degraded,
        "sha256": {"stdout": sha(stdout_path), "stderr": sha(stderr_path)},
    }


def main():
    protocol_path = HERE / "pipeline_protocol.json"
    protocol = json.loads(protocol_path.read_text())
    assert protocol["status"] == "FROZEN"
    assert protocol["worker_count"] == 1 and protocol["target_count"] == 1
    for path, digest in protocol["sources"].items():
        assert sha(Path(path)) == digest, path
    result_path = HERE / "pipeline_result.json"
    targets_path = HERE / "target_candidates.json"
    started_path = HERE / "pipeline_started.json"
    if any(path.exists() for path in (result_path, targets_path, started_path)):
        raise FileExistsError("pipeline already started")
    began = time.monotonic_ns()
    deadline = began+protocol["total_wall_cap_seconds"]*1_000_000_000
    result = {
        "status": "RUNNING", "kind": protocol["kind"],
        "candidate_id": None, "run_id": None,
        "target_count": 1, "target_kind": "constructed_correctness_control",
        "worker_count": 1, "attempts": [],
        "target_derivation": None,
        "complete_one_target_online_wall_ns": None,
        "source_sha256": {"protocol": sha(protocol_path),
                          "runner": sha(Path(__file__))},
    }
    save(started_path, {"started_utc": datetime.now(timezone.utc).isoformat(),
                        "protocol_sha256": sha(protocol_path),
                        "deadline_monotonic_ns": deadline})
    save(result_path, result)
    derivation = run_one(
        [str(SAGE), "-python", str(HERE / "derive_targets_sage.py"), str(targets_path)],
        HERE / "derive", deadline, protocol["rss_cap_bytes"])
    result["target_derivation"] = derivation
    save(result_path, result)
    if derivation["exit_code"] != 0 or derivation["stop_reason"] or not targets_path.exists():
        result["status"] = "DERIVATION_CENSORED_OR_FAILED"
        result["partial_target_dependent_parent_wall_ns"] = time.monotonic_ns()-began
        save(result_path, result)
        return
    targets = json.loads(targets_path.read_text())
    preview = json.loads((HERE / "preview_targets.json").read_text())
    if (targets["status"] != "PASS_PUBLIC_POINT_TO_ALL_RIGHT_BLOCK_CANDIDATES" or
            targets["rows"] != preview["rows"] or
            targets["torsion_point"] != preview["torsion_point"] or
            targets["candidate_count"] != 8 or
            targets["distinct_candidate_count"] != 8):
        result["status"] = "DERIVATION_REPLAY_MISMATCH"
        result["target_candidates_sha256"] = sha(targets_path)
        save(result_path, result)
        return
    result["target_candidates_sha256"] = sha(targets_path)
    support = GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
    candidates = [(row["preimage_index"], right)
                  for row in targets["rows"] for right in row["right_roots"]]
    for index, (preimage_index, right) in enumerate(candidates):
        if time.monotonic_ns() >= deadline:
            result["status"] = "CENSORED_TOTAL_WALL"
            break
        attempt_dir = HERE / f"attempt_{index:02d}"
        attempt_dir.mkdir()
        input_path = attempt_dir / "input.txt"
        input_path.write_text(f"131 18 64 96 10 2 {right}\n")
        native_path = attempt_dir / "native_result.json"
        remaining = max(1, (deadline-time.monotonic_ns())//1_000_000_000)
        command = [str(HERE / "native_right"), str(input_path),
                   str(native_path), str(remaining),
                   str(protocol["rss_cap_bytes"]), str(support)]
        row = run_one(command, attempt_dir / "solver", deadline,
                      protocol["rss_cap_bytes"])
        row.update({"index": index, "preimage_index": preimage_index,
                    "right_reciprocal": right, "input_sha256": sha(input_path),
                    "native_result_sha256": sha(native_path) if native_path.exists() else None})
        if native_path.exists():
            native = json.loads(native_path.read_text())
            row["native_status"] = native["status"]
            row["processed_first_products"] = native["processed_product_states"]
            row["raw_gcd_hits"] = len(native["hits"])
            row["native_query_ns"] = native["query_ns"]
            row["native_setup_ns"] = native["setup_ns"]
        result["attempts"].append(row)
        save(result_path, result)
        print(json.dumps({k: row.get(k) for k in
                          ("index", "native_status", "raw_gcd_hits", "wall_ns")}), flush=True)
        if (row["exit_code"] != 0 or row["stop_reason"] or
                row.get("native_status") != "COMPLETE_ALGEBRAIC_SCAN"):
            result["status"] = "NATIVE_CENSORED_OR_FAILED"
            break
    else:
        result["status"] = "COMPLETE_ALL_TARGET_DERIVED_RIGHT_CANDIDATES"
    result["phase_wall_ns"] = {
        "T_target_query": derivation["wall_ns"],
        "T_target_PDP": sum(row["wall_ns"] for row in result["attempts"]),
        "T_target_relation_check": None,
        "T_target_descent": None,
        "T_target_recovery_check": None,
    }
    result["partial_target_dependent_parent_wall_ns"] = time.monotonic_ns()-began
    result["unassigned_parent_overhead_ns"] = (
        result["partial_target_dependent_parent_wall_ns"] -
        result["phase_wall_ns"]["T_target_query"] -
        result["phase_wall_ns"]["T_target_PDP"])
    result["peak_sampled_combined_rss_bytes"] = max(
        [derivation["sampled_peak_combined_rss_bytes"]] +
        [row["sampled_peak_combined_rss_bytes"] for row in result["attempts"]])
    save(result_path, result)
    print(result["status"], len(result["attempts"]), flush=True)


if __name__ == "__main__":
    main()
