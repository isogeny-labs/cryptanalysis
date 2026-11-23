"""Bounded same-formula XOR-matrix policy diagnostic for N131 W18."""

import gzip
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n131_w18_inverse_trace_terminal_20261011"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
CONFLICT_CAP = 20_000
SOLVER_SECONDS = 120
PARENT_SECONDS = 180
RSS_CAP = 4 * 1024**3
COMMON = ["--threads=1", f"--maxconfl={CONFLICT_CAP}",
          f"--maxtime={SOLVER_SECONDS}", "--zero-exit-status",
          "--verb=1", "--printsol=1"]
ARMS = {"default": [],
        "matrix8": ["--maxmatrixrows=4000", "--maxmatrixcols=10000",
                    "--maxnummatrices=8"]}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def save(path, row):
    with path.open("x") as stream:
        json.dump(row, stream, indent=2, sort_keys=True)
        stream.write("\n")


def input_paths():
    return {"runner": Path(__file__), "prior_protocol": PRIOR / "protocol.json",
            "prior_query": PRIOR / "query_result.json",
            "prior_archive": PRIOR / "archive_receipt.json",
            "prior_xcnf_gzip": PRIOR / "ordinary.xcnf.gz",
            "solver": SOLVER.resolve()}


def freeze():
    archive = json.loads((PRIOR / "archive_receipt.json").read_text())
    query = json.loads((PRIOR / "query_result.json").read_text())
    compressed = PRIOR / "ordinary.xcnf.gz"
    assert archive["ordinary"]["gzip_sha256"] == sha(compressed)
    assert archive["ordinary"]["raw_sha256"] == query["formula"]["xcnf_sha256"]
    raw = HERE / "ordinary.xcnf"
    with gzip.open(compressed, "rb") as source, raw.open("xb") as target:
        while chunk := source.read(1 << 20):
            target.write(chunk)
    assert sha(raw) == archive["ordinary"]["raw_sha256"]
    save(HERE / "protocol.json", {
        "status": "FROZEN_SAME_FORMULA_MATRIX_POLICY_DIAGNOSTIC",
        "candidate_id": None, "curve_id": query["curve_id"],
        "workload_id": query["workload_id"],
        "public_target": query["public_target"],
        "source_formula_sha256": sha(raw),
        "source_formula_bytes": raw.stat().st_size,
        "arms": {key: COMMON + value for key, value in ARMS.items()},
        "order": ["default", "matrix8"],
        "solver_conflict_cap": CONFLICT_CAP,
        "solver_seconds_cap": SOLVER_SECONDS,
        "parent_wall_seconds_cap": PARENT_SECONDS,
        "combined_rss_cap_bytes": RSS_CAP,
        "source_sha256": {key: sha(path) for key, path in input_paths().items()}})
    print("FROZEN_SAME_FORMULA_MATRIX_POLICY_DIAGNOSTIC", flush=True)


def protocol():
    row = json.loads((HERE / "protocol.json").read_text())
    assert row["status"] == "FROZEN_SAME_FORMULA_MATRIX_POLICY_DIAGNOSTIC"
    assert row["source_sha256"] == {key: sha(path) for key, path in input_paths().items()}
    assert row["source_formula_sha256"] == sha(HERE / "ordinary.xcnf")
    return row


def run_arm(name):
    frozen = protocol()
    assert name in ARMS and frozen["arms"][name] == COMMON + ARMS[name]
    outpath, errpath = HERE / (name + ".stdout.txt"), HERE / (name + ".stderr.txt")
    parent = psutil.Process()
    t0 = time.monotonic_ns()
    peak, cpu_sample, stop = 0, 0.0, None
    with outpath.open("x") as stdout, errpath.open("x") as stderr:
        process = subprocess.Popen([str(SOLVER), *frozen["arms"][name],
                                    str(HERE / "ordinary.xcnf")],
                                   stdout=stdout, stderr=stderr)
        child = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                combined = parent.memory_info().rss + child.memory_info().rss
                cpu = child.cpu_times()
                cpu_sample = max(cpu_sample, cpu.user + cpu.system)
            except psutil.NoSuchProcess:
                combined = parent.memory_info().rss
            peak = max(peak, combined)
            if combined > RSS_CAP:
                stop = "RSS_CAP"
                process.kill()
                break
            if time.monotonic_ns() - t0 > PARENT_SECONDS * 10**9:
                stop = "PARENT_WALL_CAP"
                process.kill()
                break
            time.sleep(0.05)
        code = process.wait()
    wall_ns = time.monotonic_ns() - t0
    output = outpath.read_text(errors="replace")
    status = ("SAT_PENDING_GROUP_REPLAY" if "s SATISFIABLE" in output else
              "UNSAT" if "s UNSATISFIABLE" in output else "BOUNDED_UNKNOWN")
    matrix_lines = [line for line in output.splitlines() if line.startswith("c [matrix]")]
    restarts = [line for line in output.splitlines() if re.match(r"^c rst\s", line)]
    save(HERE / (name + ".result.json"), {
        "status": status, "arm": name, "candidate_id": None,
        "curve_id": frozen["curve_id"], "workload_id": frozen["workload_id"],
        "public_target": frozen["public_target"],
        "source_formula_sha256": frozen["source_formula_sha256"],
        "solver_flags": frozen["arms"][name],
        "solver_exit_code": code, "stop_reason": stop,
        "solver_stage_wall_ns": wall_ns,
        "solver_cpu_seconds_sampled": cpu_sample,
        "peak_combined_rss_bytes_sampled": peak,
        "matrix_accepted_lines": sum("Good   matrix" in line for line in matrix_lines),
        "matrix_too_many_rows_lines": sum("Too many rows" in line for line in matrix_lines),
        "matrix_too_many_columns_lines": sum("Too many columns" in line for line in matrix_lines),
        "last_restart_line": restarts[-1] if restarts else None,
        "restart_rows": len(restarts),
        "stdout_sha256": sha(outpath), "stderr_sha256": sha(errpath),
        "protocol_sha256": sha(HERE / "protocol.json")})
    print(name, status, f"cpu={cpu_sample:.3f}s", f"wall={wall_ns/1e9:.3f}s",
          flush=True)


def audit():
    frozen = protocol()
    rows = {}
    for name in frozen["order"]:
        row = json.loads((HERE / (name + ".result.json")).read_text())
        output = (HERE / (name + ".stdout.txt")).read_text(errors="replace")
        assert row["arm"] == name and row["solver_flags"] == frozen["arms"][name]
        assert row["source_formula_sha256"] == frozen["source_formula_sha256"]
        assert row["protocol_sha256"] == sha(HERE / "protocol.json")
        assert row["stdout_sha256"] == sha(HERE / (name + ".stdout.txt"))
        assert row["stderr_sha256"] == sha(HERE / (name + ".stderr.txt"))
        assert "c [find&init matx]" in output and row["restart_rows"] > 0
        assert row["peak_combined_rss_bytes_sampled"] < RSS_CAP
        assert row["solver_stage_wall_ns"] <= (PARENT_SECONDS + 2) * 10**9
        assert row["status"] in ("BOUNDED_UNKNOWN", "SAT_PENDING_GROUP_REPLAY", "UNSAT")
        rows[name] = {key: row[key] for key in
                      ("status", "matrix_accepted_lines", "matrix_too_many_rows_lines",
                       "matrix_too_many_columns_lines", "restart_rows",
                       "solver_cpu_seconds_sampled", "solver_stage_wall_ns")}
    save(HERE / "audit.json", {
        "status": "PASS_SAME_FORMULA_SOLVER_STAGE_RECEIPTS",
        "candidate_id": None,
        "source_formula_sha256": frozen["source_formula_sha256"],
        "rows": rows,
        "source_sha256": {"runner": sha(Path(__file__)),
                          "protocol": sha(HERE / "protocol.json"),
                          **{name: sha(HERE / (name + ".result.json"))
                             for name in frozen["order"]}}})
    print("PASS_SAME_FORMULA_SOLVER_STAGE_RECEIPTS", flush=True)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("freeze", "default", "matrix8", "audit")
    {"freeze": freeze, "default": lambda: run_arm("default"),
     "matrix8": lambda: run_arm("matrix8"), "audit": audit}[sys.argv[1]]()
