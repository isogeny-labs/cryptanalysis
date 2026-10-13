"""Freeze one N131 first product, leaving the second product unresolved."""
import gzip
import hashlib
import importlib.util
import json
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n41_n131_fouratom_product_anf_sat_20261012"
ARCHIVE = PRIOR / "n131_positive.xcnf.gz"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
spec = importlib.util.spec_from_file_location("joint_sat", PRIOR / "run.py")
joint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(joint)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_formula(mask, destination, original):
    clauses = 14
    digest = hashlib.sha256()
    size = 0
    with gzip.open(ARCHIVE, "rb") as source, destination.open("xb") as out:
        header = source.readline()
        assert header == ("p cnf %d %d\n" %
                          (original["variables"], original["cnf_clauses"] + original["native_xor_rows"])).encode()
        out.write(("p cnf %d %d\n" %
                   (original["variables"], original["cnf_clauses"] + original["native_xor_rows"] + clauses)).encode())
        while True:
            block = source.read(1 << 20)
            if not block:
                break
            digest.update(block)
            size += len(block)
            out.write(block)
        for i in range(14):
            out.write(("%d 0\n" % (i + 1 if mask >> i & 1 else -(i + 1))).encode())
    # Check the original archived body as well as the new pinned formula.
    original_header = len(header)
    assert original_header + size == original["bytes"]
    assert hashlib.sha256(header + gzip.open(ARCHIVE, "rb").read()[original_header:]).hexdigest() == original["sha256"]
    return {"first_product_mask": mask, "pinned_clauses": clauses,
            "bytes": destination.stat().st_size, "sha256": sha(destination)}


def one(mask, label, protocol, original):
    start = time.monotonic_ns()
    path = HERE / (label + ".xcnf")
    form = make_formula(mask, path, original)
    ready = time.monotonic_ns()
    command = [str(SOLVER), "--threads=1", "--xor=0", "--printsol=1",
               "--random=20261012", "--maxconfl=20000000", str(path)]
    output_path = HERE / (label + ".stdout.txt")
    cap = protocol["solver_wall_cap_seconds_each"]
    peak = 0
    timeout = rss_cap = False
    with output_path.open("x") as output:
        process = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT, text=True)
        monitor = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                peak = max(peak, monitor.memory_info().rss)
            except psutil.NoSuchProcess:
                break
            if peak > protocol["rss_cap_bytes"]:
                rss_cap = True
                process.kill()
                break
            if (time.monotonic_ns() - ready) / 1e9 > cap:
                timeout = True
                process.kill()
                break
            time.sleep(0.02)
        process.wait()
    solved = time.monotonic_ns()
    stdout = output_path.read_text()
    status = ("RSS_CAP" if rss_cap else "TIMEOUT" if timeout else
              "SAT" if "s SATISFIABLE" in stdout else
              "UNSAT" if "s UNSATISFIABLE" in stdout else "UNKNOWN")
    check = semantic = None
    if status == "SAT":
        bits = joint.model(stdout, original["variables"])
        check = joint.check_formula(path, bits)
        words, low, left, right, matrix, anf = joint.source("n131_positive")
        semantic = joint.semantic("n131_positive", bits, left, right, matrix,
                                  anf, words[0], low)
    audited = time.monotonic_ns()
    receipt = {"label": label, "status": status, "candidate_id": None,
               "formula": form, "command": command, "returncode": process.returncode,
               "stdout_sha256": sha(output_path), "peak_solver_rss_bytes_sampled": peak,
               "phase_ns_exploratory": {"formula_pin_and_replay": ready - start,
                                         "solver": solved - ready,
                                         "model_check": audited - solved},
               "formula_check": check, "semantic_check": semantic,
               "cap": {"solver_wall_s": cap, "rss_bytes": protocol["rss_cap_bytes"]}}
    (HERE / (label + ".json")).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(label, status, receipt["phase_ns_exploratory"], flush=True)


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    for name, path in (("runner", HERE / "run.py"), ("joint_runner", PRIOR / "run.py"),
                       ("solver", SOLVER), ("archived_formula_gzip", ARCHIVE)):
        assert sha(path) == protocol["sha256"][name]
    original = json.loads((PRIOR / "n131_positive.json").read_text())["formula"]
    assert original["sha256"] == protocol["original_xcnf_sha256"]
    for label, mask in (("source_first_product", 5576), ("other_first_product", 0)):
        one(mask, label, protocol, original)


if __name__ == "__main__":
    main()
