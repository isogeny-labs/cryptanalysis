"""Compare the same-formula solver traces without assigning a speedup."""

import gzip
import hashlib
import json
import shlex
from pathlib import Path

BASE = Path(__file__).resolve().parent
BASELINE = BASE / "baseline_stdout.txt.gz"
LARGE = BASE / "large_matrix_R1/cryptominisat.stdout.txt"
ATTEMPT = BASE / "source_attempt.json"
PROTOCOL = BASE / "protocol.json"
AUDIT = BASE / "large_matrix_R1/independent_terminal_audit.json"
OUTPUT = BASE / "comparison.json"


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return sha_bytes(path.read_bytes())


def command(lines):
    match = [line for line in lines if "Executed with command line:" in line]
    assert len(match) == 1
    return shlex.split(match[0].split("Executed with command line:", 1)[1].strip())


def last_restart(lines):
    rows = [line for line in lines if line.startswith("c rst")]
    assert rows
    return rows[-1]


def main():
    attempt = json.loads(ATTEMPT.read_text())
    protocol = json.loads(PROTOCOL.read_text())
    audit = json.loads(AUDIT.read_text())
    baseline_bytes = gzip.decompress(BASELINE.read_bytes())
    assert sha_bytes(baseline_bytes) == attempt["query_details"]["attempts"][0]["stdout_sha256"]
    baseline = baseline_bytes.decode(errors="replace").splitlines()
    large = LARGE.read_text(errors="replace").splitlines()
    baseline_command = command(baseline)
    large_command = command(large)
    assert baseline_command[0] == large_command[0] == "/opt/homebrew/bin/cryptominisat5"
    baseline_flags = baseline_command[1:-1]
    large_flags = large_command[1:-1]
    assert baseline_command[-1].endswith("/precomputation/target_00001/model_01/query.xcnf")
    assert large_command[-1] == str(BASE / "query.xcnf")
    assert large_flags == protocol["solver_flags"]
    assert len(baseline_flags) == len(large_flags)
    changes = [(left, right) for left, right in zip(baseline_flags, large_flags)
               if left != right]
    assert changes == [
        ("--maxtime=598.000", "--maxtime=118.000"),
        ("--maxmatrixrows=10000", "--maxmatrixrows=40000"),
        ("--maxmatrixcols=15000", "--maxmatrixcols=85000")]
    assert any("UNused matrix" in line and "36627 x38097" in line for line in baseline)
    assert audit["large_matrix_admitted"] is True
    assert audit["status"] == "CENSORED_TIME"
    assert not any(line.startswith("s SATISFIABLE") for line in baseline + large)
    assert any("TODO disable matrix, performing badly" in line for line in large)
    output = {
        "kind": "n131_d13_m12_same_formula_large_matrix_trace_comparison_v1",
        "status": "PASS_SAME_FORMULA_SEED_AND_TRACE_COMPARISON",
        "identical_formula_sha256": protocol["source_sha256"]["formula"],
        "solver_flag_changes": changes,
        "baseline_large_matrix_admitted": False,
        "preflight_large_matrix_admitted": True,
        "baseline_last_restart_line": last_restart(baseline),
        "preflight_last_restart_line": last_restart(large),
        "preflight_solver_self_diagnosis": "TODO disable matrix, performing badly",
        "baseline_status": attempt["status"],
        "preflight_status": audit["status"],
        "source_sha256": {"baseline_stdout_gzip": sha(BASELINE),
                          "baseline_stdout_uncompressed": sha_bytes(baseline_bytes),
                          "large_stdout": sha(LARGE), "attempt": sha(ATTEMPT),
                          "protocol": sha(PROTOCOL), "audit": sha(AUDIT),
                          "script": sha(Path(__file__))},
    }
    with OUTPUT.open("x") as stream:
        json.dump(output, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(output["status"])


if __name__ == "__main__":
    main()
