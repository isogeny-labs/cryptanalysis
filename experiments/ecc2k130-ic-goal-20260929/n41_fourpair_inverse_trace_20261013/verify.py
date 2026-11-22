"""Read-only audit for the N41 inverse-trace four-pair search."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
BASE = GOAL / "n131_w18_allseed_fourpair_20261012"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    build_protocol = json.loads((HERE / "protocol.json").read_text())
    build = json.loads((HERE / "build_result.json").read_text())
    query_protocol = json.loads((HERE / "query_protocol.json").read_text())
    query = json.loads((HERE / "query_result.json").read_text())
    build_paths = {"builder": HERE / "build.py", "parent": BASE / "fourpair_v2.py",
                   "fixture": BASE / "n41_diagonal/control_fixture.json",
                   "support": GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json",
                   "solver": Path(build_protocol["solver_path"])}
    assert {key: sha(path) for key, path in build_paths.items()} == build_protocol["sha256"]
    assert build["protocol_sha256"] == sha(HERE / "protocol.json")
    assert build["formula_sha256"] == sha(HERE / "public.xcnf")
    assert build["formula_bytes"] == (HERE / "public.xcnf").stat().st_size
    assert build["control"]["status"] == "PASS_COMPLETE_ASSIGNMENT"
    assert build["support_equivalence"] == {"tested_nonzero_masks": 255, "accepted_masks": 125}
    query_paths = {"runner": HERE / "run.py", "formula": HERE / "public.xcnf",
                   "build_result": HERE / "build_result.json", "solver": Path(query_protocol["solver_path"])}
    assert {key: sha(path) for key, path in query_paths.items()} == query_protocol["sha256"]
    assert query["protocol_sha256"] == sha(HERE / "query_protocol.json")
    assert query["stdout_sha256"] == sha(HERE / "solver.stdout")
    assert query["stderr_sha256"] == sha(HERE / "solver.stderr")
    terminal = [line for line in (HERE / "solver.stdout").read_text().splitlines()
                if line.startswith("s ")]
    assert terminal == query["solver_terminal_lines"]
    expected = ("BOUNDED_UNKNOWN" if query["stop_reason"] or "s INDETERMINATE" in terminal else
                "SAT_PENDING_MODEL_AUDIT" if "s SATISFIABLE" in terminal else
                "UNSAT" if "s UNSATISFIABLE" in terminal else "PRODUCER_FAILURE")
    assert query["status"] == expected
    baseline = json.loads((BASE / "v2_n41_control.json").read_text())
    assert baseline["control_check"]["status"] == "PASS_COMPLETE_CONSTRUCTED_ASSIGNMENT"
    comparison = {key: {"bdd": baseline[key if key != "formula_bytes" else key],
                        "inverse_trace": build[key if key != "formula_bytes" else key]}
                  for key in ("variables", "formula_bytes")}
    result = {"status": "PASS_RECEIPT_AND_SOURCE_AUDIT", "query_status": expected,
              "formula_comparison": comparison, "source_masks": 125,
              "public_target": query_protocol["public_target"]}
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
