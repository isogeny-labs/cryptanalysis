"""Bounded one-worker SAT checks for both pinned N41 group controls."""

import hashlib
import json
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def solve(variant, protocol):
    start = time.monotonic_ns()
    parent = psutil.Process()
    peak, samples, stop = 0, 0, None
    stdout, stderr = HERE / f"control_{variant}.solver.stdout", HERE / f"control_{variant}.solver.stderr"
    with stdout.open("xb") as out, stderr.open("xb") as err:
        child = subprocess.Popen([protocol["solver_path"], *protocol["solver_flags"],
                                  str(HERE / f"control_{variant}.xcnf")],
                                 cwd=HERE, stdout=out, stderr=err)
        proc = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                rss = parent.memory_info().rss + proc.memory_info().rss
                peak = max(peak, rss)
                samples += 1
            except psutil.NoSuchProcess:
                pass
            if peak > protocol["rss_cap_bytes"]:
                stop = "RSS_CAP"
            elif time.monotonic_ns()-start > protocol["wall_cap_seconds"]*10**9:
                stop = "WALL_CAP"
            if stop:
                child.kill()
                break
            time.sleep(0.05)
        code = child.wait()
    text = stdout.read_text()
    terminal = [line for line in text.splitlines() if line.startswith("s ")]
    status = ("BOUNDED_UNKNOWN" if stop else
              "SAT_PENDING_MODEL_CHECK" if "s SATISFIABLE" in terminal else
              "UNSAT" if "s UNSATISFIABLE" in terminal else "PRODUCER_FAILURE")
    return {"variant": variant, "status": status, "stop_reason": stop,
            "returncode": code, "terminal": terminal,
            "wall_ns": time.monotonic_ns()-start,
            "peak_sampled_parent_plus_solver_rss_bytes": peak,
            "rss_samples": samples,
            "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr)}


def main():
    protocol = json.loads((HERE / "control_run_protocol.json").read_text())
    files = {"runner": HERE / "control_run.py",
             "build": HERE / "source_control_build_result.json",
             "solver": Path(protocol["solver_path"]),
             "two_s3_links": HERE / "control_two_s3_links.xcnf",
             "direct_s4": HERE / "control_direct_s4.xcnf"}
    assert protocol["status"] == "FROZEN"
    assert protocol["sha256"] == {key: sha(path) for key, path in files.items()}
    rows = []
    for variant in protocol["run_order"]:
        row = solve(variant, protocol)
        rows.append(row)
        print(json.dumps({"variant": variant, "status": row["status"],
                          "wall_seconds": row["wall_ns"]/1e9}, sort_keys=True), flush=True)
    result = {"status": "PAIRED_PINNED_CONTROL_QUERY_COMPLETE",
              "protocol_sha256": sha(HERE / "control_run_protocol.json"),
              "rows": rows}
    (HERE / "control_run_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
