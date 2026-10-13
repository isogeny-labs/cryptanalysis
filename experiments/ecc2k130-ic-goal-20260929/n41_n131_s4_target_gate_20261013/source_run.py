"""Bounded, paired single-worker SAT query on the same N41 public point."""

import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def solve(variant, solver, flags, wall_cap, rss_cap):
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = time.monotonic_ns()
    parent = psutil.Process()
    peak = 0
    samples = 0
    stop = None
    stdout = HERE / f"public_{variant}.solver.stdout"
    stderr = HERE / f"public_{variant}.solver.stderr"
    assert not stdout.exists() and not stderr.exists()
    with stdout.open("xb") as out, stderr.open("xb") as err:
        child = subprocess.Popen([str(solver), *flags,
                                  str(HERE / f"public_{variant}.xcnf")],
                                 cwd=HERE, stdout=out, stderr=err)
        proc = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                rss = parent.memory_info().rss + proc.memory_info().rss
                samples += 1
                peak = max(peak, rss)
            except psutil.NoSuchProcess:
                pass
            if peak > rss_cap:
                stop = "RSS_CAP"
            elif time.monotonic_ns() - started > wall_cap * 10**9:
                stop = "WALL_CAP"
            if stop:
                child.kill()
                break
            time.sleep(0.05)
        code = child.wait()
    ended = time.monotonic_ns()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    lines = stdout.read_text().splitlines()
    terminal = [line for line in lines if line.startswith("s ")]
    status = ("BOUNDED_UNKNOWN" if stop or "s INDETERMINATE" in terminal else
              "SAT_PENDING_MODEL_AUDIT" if "s SATISFIABLE" in terminal else
              "UNSAT" if "s UNSATISFIABLE" in terminal else "PRODUCER_FAILURE")
    return {"variant": variant, "status": status, "stop_reason": stop,
            "returncode": code, "solver_terminal_lines": terminal,
            "wall_ns": ended-started, "rss_samples": samples,
            "peak_sampled_parent_plus_solver_rss_bytes": peak,
            "child_user_seconds": after.ru_utime-before.ru_utime,
            "child_system_seconds": after.ru_stime-before.ru_stime,
            "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr)}


def main():
    protocol = json.loads((HERE / "source_run_protocol.json").read_text())
    assert protocol["status"] == "FROZEN"
    solver = Path(protocol["solver_path"])
    paths = {"runner": HERE / "source_run.py", "source_protocol": HERE / "source_protocol.json",
             "build_result": HERE / "source_build_result.json", "solver": solver,
             "two_s3_links": HERE / "public_two_s3_links.xcnf",
             "direct_s4": HERE / "public_direct_s4.xcnf"}
    assert protocol["sha256"] == {key: sha(path) for key, path in paths.items()}
    assert not (HERE / "source_run_result.json").exists()
    rows = []
    for variant in protocol["run_order"]:
        row = solve(variant, solver, protocol["solver_flags"],
                    protocol["parent_wall_cap_seconds"], protocol["rss_cap_bytes"])
        rows.append(row)
        print(json.dumps({"variant": variant, "status": row["status"],
                          "wall_seconds": row["wall_ns"]/1e9,
                          "peak_rss_bytes": row["peak_sampled_parent_plus_solver_rss_bytes"]},
                         sort_keys=True), flush=True)
    result = {"status": "PAIRED_QUERY_COMPLETE", "candidate_id": None,
              "protocol_sha256": sha(HERE / "source_run_protocol.json"),
              "public_point": protocol["public_point"], "rows": rows}
    (HERE / "source_run_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
