"""Measured repeat of the direct-S3 full-upper positive SAT control."""
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKER = HERE.parent / "n41_n131_fouratom_product_anf_sat_20261012" / "run.py"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


direct = load("direct_runner_r2", HERE / "run.py")
checker = load("explicit_xcnf_checker_r2", CHECKER)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "upper_r2_protocol.json").read_text())
    for name, path in (("runner", HERE / "run_upper_r2.py"),
                       ("direct_runner", HERE / "run.py"),
                       ("checker", CHECKER),
                       ("direct_formula", HERE / "direct_control.xcnf"),
                       ("solver", direct.SOLVER)):
        assert sha(path) == protocol["sha256"][name], name
    direct.ten.build = direct.direct_build()
    chain, rows, root, nodes, intermediates, points = direct.input_data()
    start = time.monotonic_ns()
    circuit, wires = direct.ten.build([row["standard_reciprocal"] for row in rows], root, nodes)
    built = time.monotonic_ns()
    checked, groups = direct.constructed_check(circuit, wires, chain, intermediates, points)
    checked_at = time.monotonic_ns()
    assert checked == protocol["assignment_check"]
    intermediate_units = [wire if value >> bit & 1 else -wire
                          for wireset, value in zip(wires["intermediates"], intermediates)
                          for bit, wire in enumerate(wireset)]
    units = groups["target"] + groups["selectors"] + groups["outputs"] + intermediate_units
    assert len(units) == 2538
    profile = json.loads((HERE / "construction.json").read_text())["formula"]
    # run_arm imports a module named `run`; supply the exact audited parser.
    sys.modules["run"] = checker
    status = direct.run_arm("full_upper_control_R2", HERE / "direct_control.xcnf", units,
                            profile["variables"], profile["clauses"],
                            profile["native_xor_rows"])
    (HERE / "upper_r2_build.json").write_text(json.dumps({
        "status": status, "candidate_id": None,
        "build_ns_exploratory": built - start,
        "constructed_assignment_check_ns_exploratory": checked_at - built,
        "constructed_assignment": checked}, indent=2, sort_keys=True) + "\n")
    assert status == "SAT"


if __name__ == "__main__":
    main()
