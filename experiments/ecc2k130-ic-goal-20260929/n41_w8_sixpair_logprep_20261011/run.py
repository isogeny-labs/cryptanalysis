"""Freeze and bound the 128-target N41 relation-collection panel."""

import hashlib
import json
import psutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n41_w8_sixpair_mitm_20261011"
CAP = 1800
RSS = 4 * 1024**3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def sources():
    return {"runner": HERE / "run.py", "native_source": HERE / "batch_join.cpp",
            "native_binary": HERE / "batch_join", "panel_producer": HERE / "panel_sage.py",
            "panel_protocol": HERE / "panel_protocol.json",
            "panel_result": HERE / "panel_result.json", "panel": HERE / "panel.tsv",
            "prior_group_kernel": PRIOR / "join.cpp", "prior_states": PRIOR / "join_input.tsv",
            "prior_audit": PRIOR / "audit_result.json",
            "runtime": HERE / "sage_runtime_info.json"}


def freeze():
    panel = json.loads((HERE / "panel_result.json").read_text())
    assert panel["status"] == "PASS_N41_W8_KNOWN_SCALAR_PANEL"
    assert panel["panel_sha256"] == sha(HERE / "panel.tsv")
    record = {"status": "FROZEN_N41_W8_128_TARGET_RELATION_PANEL",
              "curve_id": panel["curve_id"], "target_count": panel["target_count"],
              "raw_preimages_per_target": panel["raw_preimages_per_target"],
              "generator_mask": panel["generator_mask"],
              "generator_projected": panel["generator_projected"],
              "source_pair_seed": 184, "source_rotations": [0, 7, 14, 21, 28, 35],
              "worker_count": 1, "wall_cap_seconds": CAP,
              "combined_rss_cap_bytes": RSS,
              "compile_command": "/usr/bin/clang++ -O3 -std=c++17 -Wall -Wextra -pedantic batch_join.cpp -o batch_join",
              "source_sha256": {name: sha(path) for name, path in sources().items()}}
    save(HERE / "protocol.json", record)
    print(record["status"])


def query():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["source_sha256"] == {name: sha(path) for name, path in sources().items()}
    stdout_path, stderr_path = HERE / "batch.stdout.txt", HERE / "batch.stderr.txt"
    assert not stdout_path.exists() and not stderr_path.exists()
    parent = psutil.Process()
    started = time.monotonic()
    peak = 0
    stop = None
    with stdout_path.open("x") as stdout, stderr_path.open("x") as stderr:
        child = subprocess.Popen([str(HERE / "batch_join"),
                                  str(HERE.parent / "n41_w8_sixpair_mitm_20261011/join_input.tsv"),
                                  str(HERE / "panel.tsv")],
                                 stdout=stdout, stderr=stderr)
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
            time.sleep(0.1)
        code = child.wait()
    wall = time.monotonic() - started
    lines = stdout_path.read_text().splitlines()
    rows = [line for line in lines if line.startswith("ROW ")]
    misses = [line for line in lines if line.startswith("MISS ")]
    completed = [line for line in lines if line.startswith("COMPLETE ")]
    if stop:
        status = "CENSORED_TIME" if stop == "WALL_CAP" else "CENSORED_RSS"
    elif code == 0 and len(completed) == 1 and len(rows) + len(misses) == 128:
        status = "PANEL_COMPLETE_PENDING_SAGE_RANK_AUDIT"
    else:
        status = "PRODUCER_FAILURE"
    result = {"status": status, "candidate_id": None,
              "target_count": 128, "relation_rows_native": len(rows),
              "restricted_source_misses": len(misses),
              "completed_target_count": len(rows) + len(misses),
              "phase_lines": [line for line in lines if line.startswith(("CHECK_PASS", "LEFT_DONE", "RIGHT_DONE", "COMPLETE"))],
              "wall_seconds_exploratory": wall, "combined_peak_rss_bytes_sampled": peak,
              "stop_reason": stop, "exit_code": code,
              "stdout_sha256": sha(stdout_path), "stderr_sha256": sha(stderr_path),
              "protocol_sha256": sha(HERE / "protocol.json")}
    save(HERE / "query_result.json", result)
    print(json.dumps({"status": status, "rows": len(rows), "misses": len(misses),
                      "wall_seconds": wall, "peak_rss": peak}), flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("freeze", "query"):
        raise SystemExit("usage: run.py freeze|query")
    {"freeze": freeze, "query": query}[sys.argv[1]]()
