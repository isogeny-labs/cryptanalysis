"""Specialize the first product in the ANF before emitting native-XOR rows."""
import hashlib
import importlib.util
import json
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n41_n131_fouratom_product_anf_sat_20261012"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
spec = importlib.util.spec_from_file_location("joint_sat", PRIOR / "run.py")
joint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(joint)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def specialize(anf, first_mask, d):
    low = (1 << d) - 1
    out = {}
    for mask, value in anf.items():
        if (mask & low) & ~first_mask:
            continue
        second = mask >> d
        out[second] = out.get(second, 0) ^ value
    return {mask: value for mask, value in out.items() if value}


def run_one(label, first_mask, protocol, source):
    words, low, left, right, matrix, anf = source
    n = words[0]
    d = len(left)
    start = time.monotonic_ns()
    one = specialize(anf, first_mask, d)
    specialized = time.monotonic_ns()
    path = HERE / (label + ".small.xcnf")
    profile = joint.formula(path, n, d // 2, one)
    ready = time.monotonic_ns()
    command = [str(SOLVER), "--threads=1", "--xor=0", "--printsol=1",
               "--random=20261012", "--maxconfl=20000000", str(path)]
    output_path = HERE / (label + ".small.stdout.txt")
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
            time.sleep(0.005)
        process.wait()
    solved = time.monotonic_ns()
    stdout = output_path.read_text()
    status = ("RSS_CAP" if rss_cap else "TIMEOUT" if timeout else
              "SAT" if "s SATISFIABLE" in stdout else
              "UNSAT" if "s UNSATISFIABLE" in stdout else "UNKNOWN")
    checked = semantic = None
    if status == "SAT":
        bits = joint.model(stdout, profile["variables"])
        checked = joint.check_formula(path, bits)
        second_mask = sum(1 << i for i in range(d) if bits[i + 1])
        p = q = 0
        for i in range(d):
            if first_mask >> i & 1:
                p ^= left[i]
            if second_mask >> i & 1:
                q ^= right[i]
        direct = joint.ind.direct(matrix, p, q, n, low)
        assert direct == joint.ind.eval_anf(one, second_mask) == 0
        semantic = {"first_product_mask": first_mask,
                    "second_product_mask": second_mask, "direct_field_value": direct,
                    "matches_archived_source_products": [first_mask, second_mask] == [5576, 3]}
    audited = time.monotonic_ns()
    result = {"label": label, "status": status, "candidate_id": None,
              "specialized_anf_monomials": len(one), "formula": profile,
              "command": command, "returncode": process.returncode,
              "stdout_sha256": sha(output_path), "peak_solver_rss_bytes_sampled": peak,
              "phase_ns_exploratory": {"anf_specialize": specialized - start,
                                        "formula_emit": ready - specialized,
                                        "solver": solved - ready,
                                        "model_check": audited - solved},
              "formula_check": checked, "semantic_check": semantic,
              "cap": {"solver_wall_s": cap, "rss_bytes": protocol["rss_cap_bytes"]}}
    (HERE / (label + ".small.json")).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(label, status, len(one), profile, result["phase_ns_exploratory"], flush=True)


def main():
    protocol = json.loads((HERE / "specialized_protocol.json").read_text())
    for name, path in (("runner", HERE / "run_specialized.py"),
                       ("joint_runner", PRIOR / "run.py"), ("solver", SOLVER)):
        assert sha(path) == protocol["sha256"][name]
    started = time.monotonic_ns()
    source = joint.source("n131_positive")
    build_ns = time.monotonic_ns() - started
    (HERE / "shared_anf_build.json").write_text(json.dumps(
        {"status": "PASS_SHARED_FULL_ANF_BUILD", "anf_monomials": len(source[-1]),
         "elapsed_ns_exploratory": build_ns}, indent=2) + "\n")
    for label, mask in (("source_first_product", 5576), ("other_first_product", 0)):
        run_one(label, mask, protocol, source)


if __name__ == "__main__":
    main()
