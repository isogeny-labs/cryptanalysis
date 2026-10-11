"""Freeze and run one fresh N41 target through IC and matched rho."""

import hashlib
import json
import psutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
JOIN = HERE.parent / "n41_w8_sixpair_mitm_20261011"
LOGS = HERE.parent / "n41_w8_sixpair_logprep_20261011"
CAP = 300
RSS = 4 * 1024**3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def sources():
    return {"runner": HERE / "run.py", "online_source": HERE / "online.cpp",
            "online_binary": HERE / "online", "preparer": HERE / "prepare_sage.py",
            "preparation_protocol": HERE / "preparation_protocol.json",
            "preparation_result": HERE / "preparation_result.json",
            "state_logs": HERE / "state_logs.tsv", "torsion": HERE / "torsion.tsv",
            "public_target": HERE / "public_target.tsv",
            "smoke_target": HERE / "smoke_public.tsv",
            "smoke_output": HERE / "smoke.stdout.txt",
            "group_kernel": JOIN / "join.cpp", "source_states": JOIN / "join_input.tsv",
            "factor_logs": LOGS / "audit_result.json",
            "runtime": HERE / "sage_runtime_info.json"}


def freeze():
    prepared = json.loads((HERE / "preparation_result.json").read_text())
    assert prepared["status"] == "PASS_N41_W8_HELDOUT_INPUT_PREPARATION"
    assert prepared["state_logs_sha256"] == sha(HERE / "state_logs.tsv")
    assert prepared["torsion_sha256"] == sha(HERE / "torsion.tsv")
    assert prepared["public_target_sha256"] == sha(HERE / "public_target.tsv")
    smoke = (HERE / "smoke.stdout.txt").read_text().splitlines()
    assert smoke[0].startswith("IC_READY 2513280 2513280 ")
    assert smoke[1].startswith("IC_RESULT 445577591162 ")
    workload = {"curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
                "public_target": prepared["public_target"],
                "input_law": "SHA256 held-out one-target point, scalar sealed from solvers",
                "target_count": 1, "cold_or_warm": "one cold target after reusable tables and factor logs"}
    workload_id = hashlib.sha256(json.dumps(
        workload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:12]
    record = {"status": "FROZEN_N41_W8_HELDOUT_ONE_TARGET_IC_RHO",
              "candidate_id": None, "curve_id": workload["curve_id"],
              "workload_id": workload_id, "workload_record": workload,
              "public_target": prepared["public_target"],
              "generator_projected": prepared["generator_projected"],
              "target_count": 1, "run_order": ["ic", "rho"],
              "worker_count_each": 1, "parent_wall_cap_seconds_each": CAP,
              "combined_rss_cap_bytes_each": RSS,
              "rho_walk": "16 target-dependent additive partitions, hash partition, 8-bit x distinguished points, one worker, no cross-target state",
              "ic_online_boundary": "after source table and factor-log loading, table build, and public point input loading; before raw-preimage computation",
              "rho_online_boundary": "after public point and generator input loading; before target-dependent partition construction",
              "source_sha256": {name: sha(path) for name, path in sources().items()}}
    save(HERE / "protocol.json", record)
    print(record["status"], workload_id)


def run_mode(mode, protocol):
    outpath = HERE / f"{mode}.stdout.txt"
    errpath = HERE / f"{mode}.stderr.txt"
    assert not outpath.exists() and not errpath.exists()
    gx, gy = protocol["generator_projected"]
    if mode == "ic":
        args = [str(HERE / "online"), "ic", str(JOIN / "join_input.tsv"),
                str(HERE / "state_logs.tsv"), str(HERE / "torsion.tsv"),
                str(HERE / "public_target.tsv"), str(gx), str(gy)]
    else:
        args = [str(HERE / "online"), "rho", str(HERE / "public_target.tsv"),
                str(gx), str(gy)]
    parent = psutil.Process()
    started = time.monotonic()
    peak = 0
    stop = None
    with outpath.open("x") as stdout, errpath.open("x") as stderr:
        child = subprocess.Popen(args, stdout=stdout, stderr=stderr)
        process = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                combined = parent.memory_info().rss + process.memory_info().rss
            except psutil.NoSuchProcess:
                combined = parent.memory_info().rss
            peak = max(peak, combined)
            if combined > RSS:
                stop = "RSS_CAP"
                child.kill()
                break
            if time.monotonic() - started > CAP:
                stop = "WALL_CAP"
                child.kill()
                break
            time.sleep(0.05)
        code = child.wait()
    lines = outpath.read_text().splitlines()
    result_line = next((line for line in lines if line.startswith(
        "IC_RESULT " if mode == "ic" else "RHO_RESULT ")), None)
    if stop:
        status = "CENSORED_TIME" if stop == "WALL_CAP" else "CENSORED_RSS"
    elif code == 0 and result_line:
        status = "SCALAR_FOUND_PENDING_INDEPENDENT_SAGE_REPLAY"
    elif code == 1 and any(line.startswith("IC_MISS " if mode == "ic" else
                                            "RHO_BOUNDED ") for line in lines):
        status = "COMPLETE_RESTRICTED_SOURCE_MISS" if mode == "ic" else "BOUNDED_UNKNOWN"
    else:
        status = "PRODUCER_FAILURE"
    record = {"status": status, "mode": mode, "curve_id": protocol["curve_id"],
              "workload_id": protocol["workload_id"],
              "public_target": protocol["public_target"],
              "generator_projected": protocol["generator_projected"],
              "worker_count": 1, "parent_wall_cap_seconds": CAP,
              "combined_rss_cap_bytes": RSS,
              "full_process_wall_seconds_exploratory": time.monotonic() - started,
              "combined_peak_rss_bytes_sampled": peak,
              "exit_code": code, "stop_reason": stop,
              "result_line": result_line, "phase_lines": lines,
              "stdout_sha256": sha(outpath), "stderr_sha256": sha(errpath),
              "protocol_sha256": sha(HERE / "protocol.json")}
    save(HERE / f"{mode}_result.json", record)
    print(json.dumps({"mode": mode, "status": status,
                      "result_line": result_line,
                      "full_process_wall_seconds": record["full_process_wall_seconds_exploratory"]}),
          flush=True)
    return record


def query():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["status"] == "FROZEN_N41_W8_HELDOUT_ONE_TARGET_IC_RHO"
    assert protocol["source_sha256"] == {name: sha(path) for name, path in sources().items()}
    for mode in protocol["run_order"]:
        run_mode(mode, protocol)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("freeze", "query"):
        raise SystemExit("usage: run.py freeze|query")
    {"freeze": freeze, "query": query}[sys.argv[1]]()
