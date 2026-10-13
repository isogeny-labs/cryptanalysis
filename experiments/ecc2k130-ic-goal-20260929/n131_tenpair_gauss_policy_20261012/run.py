"""Same-formula ten-pair N131 public SAT trial with Gaussian matrices disabled."""
import gzip
import hashlib
import importlib.util
import json
import os
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
N41 = ROOT / "n41_n131_fouratom_product_anf_sat_20261012"
N131 = ROOT / "n131_w18_tenpair_binary_frob_20261012"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
spec = importlib.util.spec_from_file_location("xcnf_model_audit", N41 / "run.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def replay(source, destination, expected_hash, expected_bytes):
    digest = hashlib.sha256()
    size = 0
    with gzip.open(source, "rb") as packed, destination.open("xb") as raw:
        for block in iter(lambda: packed.read(1 << 20), b""):
            raw.write(block)
            digest.update(block)
            size += len(block)
    assert digest.hexdigest() == expected_hash and size == expected_bytes
    return {"raw_sha256": digest.hexdigest(), "raw_bytes": size,
            "gzip_sha256": sha(source)}


def run(label, source, expected, cap, parent_cap, variables, rows):
    start = time.monotonic_ns()
    formula = HERE / (label + ".xcnf")
    replayed = replay(source, formula, expected["raw_sha256"], expected["raw_bytes"])
    ready = time.monotonic_ns()
    command = [str(SOLVER), "--threads=1", "--xor=0", "--maxnummatrices=0",
               "--maxtime=%d" % cap, "--zero-exit-status", "--verb=1",
               "--printsol=1", str(formula)]
    stdout_path = HERE / (label + ".stdout.txt")
    stderr_path = HERE / (label + ".stderr.txt")
    peak = 0
    rss_cap = parent_timeout = False
    parent = psutil.Process(os.getpid())
    with stdout_path.open("x") as out, stderr_path.open("x") as err:
        child = subprocess.Popen(command, stdout=out, stderr=err)
        process = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                combined = parent.memory_info().rss + process.memory_info().rss
                peak = max(peak, combined)
            except psutil.NoSuchProcess:
                break
            if combined > 4 * 1024 ** 3:
                rss_cap = True
                child.kill()
                break
            if (time.monotonic_ns() - ready) / 1e9 > parent_cap:
                parent_timeout = True
                child.kill()
                break
            time.sleep(0.05)
        child.wait()
    stopped = time.monotonic_ns()
    stdout = stdout_path.read_text()
    statuses = [line.strip() for line in stdout.splitlines() if line.startswith("s ")]
    status = ("RSS_CAP" if rss_cap else "PARENT_TIME_CAP" if parent_timeout else
              "SAT" if "s SATISFIABLE" in statuses else
              "UNSAT" if "s UNSATISFIABLE" in statuses else
              "BOUNDED_UNKNOWN" if "s INDETERMINATE" in statuses else "UNKNOWN")
    model_check = None
    if status == "SAT":
        bits = audit.model(stdout, variables)
        model_check = audit.check_formula(formula, bits)
        assert model_check == rows
    checked = time.monotonic_ns()
    receipt = {"label": label, "status": status, "candidate_id": None,
               "archived_formula": replayed, "command": command,
               "solver_exit_code": child.returncode, "status_lines": statuses,
               "model_check": model_check, "peak_combined_rss_bytes_sampled": peak,
               "phase_ns_exploratory": {"archive_replay": ready - start,
                                         "solver_and_terminal": stopped - ready,
                                         "model_check": checked - stopped},
               "stdout_sha256": sha(stdout_path), "stderr_sha256": sha(stderr_path),
               "resource": {"workers": 1, "solver_cap_s": cap,
                            "parent_cap_s": parent_cap, "rss_cap_bytes": 4 * 1024 ** 3}}
    (HERE / (label + ".json")).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(label, status, receipt["phase_ns_exploratory"], peak, flush=True)
    return status


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    for name, path in (("runner", HERE / "run.py"),
                       ("model_audit", N41 / "run.py"),
                       ("solver", SOLVER),
                       ("n41_formula", N41 / "n41_positive.xcnf.gz"),
                       ("n131_formula", N131 / "ordinary.xcnf.gz")):
        assert sha(path) == protocol["sha256"][name], name
    smoke = run("n41_smoke", N41 / "n41_positive.xcnf.gz",
                protocol["n41_archive"], 10, 15, 4060,
                {"cnf_clauses_checked": 12138, "native_xor_rows_checked": 41})
    if smoke != "SAT":
        raise RuntimeError("Gaussian-policy correctness smoke did not return SAT")
    run("n131_public", N131 / "ordinary.xcnf.gz",
        protocol["n131_archive"], 450, 470, 258801,
        {"cnf_clauses_checked": 528856, "native_xor_rows_checked": 81074})


if __name__ == "__main__":
    main()
