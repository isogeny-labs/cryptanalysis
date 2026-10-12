"""Exercise native XOR SAT and UNSAT under the proposed matrix policy."""

import hashlib
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
tests = {
    "sat": ("p cnf 1 1\nx1 0\n", "s SATISFIABLE"),
    "unsat": ("p cnf 1 2\nx1 0\n-1 0\n", "s UNSATISFIABLE"),
}
results = {}
for label, (contents, expected) in tests.items():
    formula = HERE / (label + ".xcnf")
    formula.write_text(contents)
    completed = subprocess.run([str(SOLVER), "--threads=1", "--maxnummatrices=0",
                                "--zero-exit-status", "--verb=0", str(formula)],
                               capture_output=True, text=True, check=True)
    assert expected in completed.stdout.splitlines()
    assert completed.stderr == ""
    results[label] = {
        "expected": expected,
        "input_sha256": hashlib.sha256(formula.read_bytes()).hexdigest(),
        "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
    }
    (HERE / (label + ".stdout.txt")).write_text(completed.stdout)
result = {"status": "PASS_GAUSS0_NATIVE_XOR_SAT_UNSAT_SMOKE",
          "solver_sha256": hashlib.sha256(SOLVER.resolve().read_bytes()).hexdigest(),
          "tests": results}
(HERE / "smoke_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(result["status"])
