"""Repeat the frozen ANF-to-XCNF method on the archived N131 W15 block."""
import hashlib
import importlib.util
import json
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n41_n131_fouratom_product_anf_20261012"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
spec = importlib.util.spec_from_file_location("n41_sat_source", HERE / "run.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(case):
    protocol = json.loads((HERE / "n131_protocol.json").read_text())
    for name, path in (("runner", HERE / "run_n131.py"),
                       ("n41_runner", HERE / "run.py"),
                       ("independent_anf", PARENT / "audit.py"),
                       ("solver", SOLVER), (case, PARENT / (case + ".txt"))):
        assert sha(path) == protocol["sha256"][name], name
    start = time.monotonic_ns()
    words, low, left, right, matrix, anf = core.source(case)
    built = time.monotonic_ns()
    path = HERE / (case + ".xcnf")
    profile = core.formula(path, words[0], len(left), anf)
    ready = time.monotonic_ns()
    command = [str(SOLVER), "--threads=1", "--xor=0", "--printsol=1",
               "--random=20261012", "--maxconfl=20000000", str(path)]
    stdout_path = HERE / (case + ".stdout.txt")
    cap = protocol["solver_wall_cap_seconds_each"]
    rss_cap = protocol["rss_cap_bytes"]
    peak = 0
    timed_out = rss_exceeded = False
    with stdout_path.open("x") as output:
        process = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT, text=True)
        monitor = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                peak = max(peak, monitor.memory_info().rss)
            except psutil.NoSuchProcess:
                break
            if peak > rss_cap:
                rss_exceeded = True
                process.kill()
                break
            if (time.monotonic_ns() - ready) / 1e9 > cap:
                timed_out = True
                process.kill()
                break
            time.sleep(0.05)
        process.wait()
    solved = time.monotonic_ns()
    stdout = stdout_path.read_text()
    status = ("RSS_CAP" if rss_exceeded else "TIMEOUT" if timed_out else
              "SAT" if "s SATISFIABLE" in stdout else
              "UNSAT" if "s UNSATISFIABLE" in stdout else "UNKNOWN")
    checked = meaning = None
    if status == "SAT":
        bits = core.model(stdout, profile["variables"])
        checked = core.check_formula(path, bits)
        meaning = core.semantic(case, bits, left, right, matrix, anf, words[0], low)
    audited = time.monotonic_ns()
    result = {"case": case, "status": status, "candidate_id": None,
              "formula": profile, "anf_monomials": len(anf), "command": command,
              "solver_returncode": process.returncode,
              "solver_stdout_sha256": sha(stdout_path),
              "peak_solver_rss_bytes_sampled": peak,
              "phase_ns_exploratory": {"anf_build": built - start,
                                        "formula_emit": ready - built,
                                        "solver": solved - ready,
                                        "model_and_semantic_check": audited - solved},
              "formula_model_check": checked, "semantic_check": meaning,
              "resource": {"workers": 1, "solver_wall_cap_s": cap,
                           "rss_cap_bytes": rss_cap}}
    (HERE / (case + ".json")).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(case, status, profile, result["phase_ns_exploratory"], flush=True)


if __name__ == "__main__":
    for name in ("n131_positive", "n131_control"):
        run(name)
