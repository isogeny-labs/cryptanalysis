"""Matched constructed-target CryptoMiniSat matrix-policy gate."""

import gzip
import hashlib
import json
import os
import resource
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n131_w18_tenpair_binary_frob_20261012"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
BASE_FLAGS = ["--threads=1", "--maxtime=110", "--zero-exit-status",
              "--verb=1", "--printsol=1"]
ARMS = {"default": BASE_FLAGS,
        "nogauss": BASE_FLAGS + ["--maxnummatrices=0"]}
WALL_CAP_SECONDS = 120
RSS_CAP_BYTES = 4 * 1024**3


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def save(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def source_hashes():
    return {"source_protocol": sha(SOURCE / "protocol.json"),
            "source_control": sha(SOURCE / "control_result.json"),
            "source_archive": sha(SOURCE / "archive_receipt.json"),
            "source_formula_gzip": sha(SOURCE / "control.xcnf.gz"),
            "source_sage_replay": sha(SOURCE / "sage_fixture_result.json"),
            "runner": sha(Path(__file__)), "solver": sha(SOLVER)}


def freeze():
    source = load(SOURCE / "protocol.json")
    control = load(SOURCE / "control_result.json")
    archive = load(SOURCE / "archive_receipt.json")
    assert source["curve_id"] == "EC1N131Ckb1heb5f1998f20b"
    assert control["status"] == "PASS_FULL_N131_TENPAIR_ORBIT_CONSTRUCTED_WITNESS"
    assert control["assignment_check"] == {
        "clauses": control["formula"]["clauses"],
        "native_xor_rows": control["formula"]["native_xor_rows"]}
    assert control["formula"]["xcnf_sha256"] == archive["formulas"]["control"]["raw_sha256"]
    assert sha(SOURCE / "control.xcnf.gz") == archive["formulas"]["control"]["gzip_sha256"]
    save("protocol.json", {"status": "FROZEN_BEFORE_MATCHED_SOLVER_ARMS",
                           "candidate_id": None, "curve_id": source["curve_id"],
                           "constructed_public_target": control["constructed_public_target"],
                           "formula_sha256": control["formula"]["xcnf_sha256"],
                           "formula_bytes": control["formula"]["xcnf_bytes"],
                           "formula_variables": control["formula"]["variables"],
                           "formula_clauses": control["formula"]["clauses"],
                           "formula_xor_rows": control["formula"]["native_xor_rows"],
                           "arm_order": ["default", "nogauss"],
                           "solver_flags": ARMS,
                           "wall_cap_seconds_per_arm": WALL_CAP_SECONDS,
                           "rss_cap_bytes": RSS_CAP_BYTES,
                           "source_sha256": source_hashes(),
                           "solver_path": str(SOLVER)})


def prepare_formula():
    frozen = load(HERE / "protocol.json")
    assert frozen["source_sha256"] == source_hashes()
    formula = HERE / "control.xcnf"
    assert not formula.exists()
    started = time.monotonic_ns()
    with gzip.open(SOURCE / "control.xcnf.gz", "rb") as source, formula.open("xb") as target:
        for block in iter(lambda: source.read(1 << 20), b""):
            target.write(block)
    elapsed = time.monotonic_ns() - started
    assert sha(formula) == frozen["formula_sha256"]
    assert formula.stat().st_size == frozen["formula_bytes"]
    save("formula_prepare.json", {"status": "PASS_FORMULA_BYTE_REPLAY",
                                  "sha256": frozen["formula_sha256"],
                                  "bytes": frozen["formula_bytes"],
                                  "decompression_ns_excluded_from_solver": elapsed,
                                  "protocol_sha256": sha(HERE / "protocol.json")})


def run_arm(arm):
    frozen = load(HERE / "protocol.json")
    prepared = load(HERE / "formula_prepare.json")
    assert frozen["source_sha256"] == source_hashes()
    assert prepared["sha256"] == sha(HERE / "control.xcnf")
    assert prepared["protocol_sha256"] == sha(HERE / "protocol.json")
    assert frozen["solver_flags"] == ARMS
    assert arm in ARMS
    if arm == "nogauss":
        assert load(HERE / "default_result.json")["status"] != "PRODUCER_FAILURE"
    stdout_path = HERE / f"{arm}.stdout.txt"
    stderr_path = HERE / f"{arm}.stderr.txt"
    parent = psutil.Process()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    load_before = list(os.getloadavg())
    peak, stop_reason = 0, None
    started = time.monotonic_ns()
    with stdout_path.open("x") as stdout, stderr_path.open("x") as stderr:
        process = subprocess.Popen([str(SOLVER), *ARMS[arm], str(HERE / "control.xcnf")],
                                   stdout=stdout, stderr=stderr)
        child = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                combined = parent.memory_info().rss + child.memory_info().rss
            except psutil.NoSuchProcess:
                combined = parent.memory_info().rss
            peak = max(peak, combined)
            if combined > RSS_CAP_BYTES:
                stop_reason = "RSS_CAP"
            elif time.monotonic_ns() - started >= WALL_CAP_SECONDS * 10**9:
                stop_reason = "WALL_CAP"
            if stop_reason:
                process.kill()
                break
            time.sleep(0.05)
        exit_code = process.wait()
    ended = time.monotonic_ns()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    output = stdout_path.read_text(errors="replace")
    stderr = stderr_path.read_text(errors="replace")
    lines = [line for line in output.splitlines() if line.startswith("s ")]
    elapsed = (ended-started)/1e9
    if stop_reason == "RSS_CAP":
        status = "CENSORED_RSS"
    elif stop_reason == "WALL_CAP" or (lines == ["s INDETERMINATE"] and elapsed >= 105):
        status = "CENSORED_TIME"
    elif lines == ["s SATISFIABLE"]:
        status = "SAT_PENDING_INDEPENDENT_REPLAY"
    elif lines == ["s UNSATISFIABLE"]:
        status = "UNSAT_CONTRADICTS_CONSTRUCTED_ASSIGNMENT"
    else:
        status = "PRODUCER_FAILURE"
    save(f"{arm}_result.json", {
        "status": status, "solver_status_lines": lines,
        "solver_started": "CryptoMiniSat version" in output and
                          "c -- xor clauses added:" in output,
        "exit_code": exit_code, "stop_reason": stop_reason,
        "elapsed_seconds_exploratory": elapsed,
        "child_cpu_seconds": (after.ru_utime-before.ru_utime) +
                             (after.ru_stime-before.ru_stime),
        "sampled_peak_combined_rss_bytes": peak,
        "actual_restart_rows": sum(line.startswith("c rst") for line in output.splitlines()),
        "gauss_disable_diagnostics": output.count("TODO disable matrix, performing badly"),
        "matrix_initialization_rows": sum("[matrix]" in line for line in output.splitlines()),
        "stderr_bytes": stderr_path.stat().st_size,
        "stdout_sha256": sha(stdout_path), "stderr_sha256": sha(stderr_path),
        "protocol_sha256": sha(HERE / "protocol.json"),
        "formula_sha256": frozen["formula_sha256"],
        "solver_flags": ARMS[arm], "arm": arm,
        "host_loadavg_before_after": [load_before, list(os.getloadavg())],
    })
    print(arm, status, elapsed, peak, flush=True)


if __name__ == "__main__":
    import sys
    command = sys.argv[1]
    if command == "freeze":
        freeze()
    elif command == "prepare":
        prepare_formula()
    elif command == "run":
        run_arm(sys.argv[2])
    else:
        raise SystemExit("usage: run.py freeze|prepare|run default|run nogauss")
