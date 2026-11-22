"""Independently check the saved R1 direct-S3 SAT model after runner import failure."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKER = HERE.parent / "n41_n131_fouratom_product_anf_sat_20261012" / "run.py"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    spec = importlib.util.spec_from_file_location("explicit_xcnf_checker", CHECKER)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    formula = HERE / "full_upper_control.xcnf"
    stdout_path = HERE / "full_upper_control.stdout.txt"
    stderr_path = HERE / "full_upper_control.stderr.txt"
    stdout = stdout_path.read_text()
    assert "s SATISFIABLE" in stdout.splitlines()
    profile = json.loads((HERE / "construction.json").read_text())["formula"]
    bits = checker.model(stdout, profile["variables"])
    checked = checker.check_formula(formula, bits)
    assert checked == {"cnf_clauses_checked": profile["clauses"] + 2538,
                       "native_xor_rows_checked": profile["native_xor_rows"]}
    receipt = {"status": "PASS_R1_DIRECT_S3_SAT_MODEL_POSTRUN_AUDIT",
               "candidate_id": None, "model_variables": len(bits),
               "formula_check": checked, "formula_sha256": sha(formula),
               "stdout_sha256": sha(stdout_path), "stderr_sha256": sha(stderr_path),
               "runner_failure": "AttributeError: module run has no attribute model after SAT terminal"}
    (HERE / "full_upper_control_R1_audit.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(receipt["status"], checked, flush=True)


if __name__ == "__main__":
    main()
