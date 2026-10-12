"""Audit the same-formula matrix-policy receipts and terminal statuses."""

import gzip
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n131_w18_tenpair_binary_frob_20261012"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / "protocol.json").read_text())
parent_protocol = json.loads((PARENT / "protocol.json").read_text())
parent_query = json.loads((PARENT / "query_result.json").read_text())
parent_archive = json.loads((PARENT / "archive_receipt.json").read_text())
smoke = json.loads((HERE / "smoke_result.json").read_text())
assert protocol["status"] == "FROZEN_N131_TENPAIR_GAUSS0_SOLVER_VARIANT"
assert smoke["status"] == "PASS_GAUSS0_NATIVE_XOR_SAT_UNSAT_SMOKE"
assert protocol["curve_id"] == parent_protocol["curve_id"]
assert protocol["workload_id"] == parent_protocol["workload_id"]
assert protocol["public_target"] == parent_protocol["public_target"]
assert protocol["worker_count"] == parent_protocol["worker_count"] == 1
assert protocol["combined_rss_cap_bytes"] == parent_protocol["combined_rss_cap_bytes"]
assert protocol["ordinary_total_wall_cap_seconds"] == parent_protocol["total_target_dependent_cap_seconds"] == 600
assert protocol["sha256"]["parent_query"] == sha(PARENT / "query_result.json")
assert protocol["sha256"]["parent_archive"] == sha(PARENT / "archive_receipt.json")
assert parent_query["status"] == "BOUNDED_UNKNOWN"
assert parent_query["status_lines"] == ["s INDETERMINATE"]

results = {}
for mode in ("control", "ordinary"):
    receipt = json.loads((HERE / (mode + "_result.json")).read_text())
    output = (HERE / (mode + ".stdout.txt")).read_text(errors="replace")
    stderr = (HERE / (mode + ".stderr.txt")).read_text(errors="replace")
    assert receipt["mode"] == mode
    assert receipt["protocol_sha256"] == sha(HERE / "protocol.json")
    assert receipt["formula_sha256"] == protocol["source_formula_sha256"][mode]
    assert receipt["formula_sha256"] == parent_archive["formulas"][mode]["raw_sha256"]
    with gzip.open(PARENT / (mode + ".xcnf.gz"), "rb") as stream:
        assert hashlib.sha256(stream.read()).hexdigest() == receipt["formula_sha256"]
    assert receipt["stdout_sha256"] == sha(HERE / (mode + ".stdout.txt"))
    assert receipt["stderr_sha256"] == sha(HERE / (mode + ".stderr.txt"))
    assert stderr == ""
    assert receipt["status_lines"] == [line for line in output.splitlines()
                                       if line.startswith("s ")]
    assert receipt["actual_restart_rows"] == sum(
        line.startswith("c rst") for line in output.splitlines())
    assert receipt["matrix_disable_diagnostics"] == sum(
        line.startswith("c TODO disable matrix") for line in output.splitlines())
    assert receipt["matrix_disable_diagnostics"] == 0
    assert receipt["worker_count"] == 1
    assert receipt["peak_combined_rss_bytes_sampled"] <= protocol["combined_rss_cap_bytes"]
    assert "--maxnummatrices=0" in receipt["solver_flags"]
    assert receipt["status"] in ("BOUNDED_UNKNOWN", "SAT_PENDING_GROUP_REPLAY", "UNSAT")
    if receipt["status"] == "BOUNDED_UNKNOWN":
        assert receipt["status_lines"] in ([], ["s INDETERMINATE"])
    results[mode] = {"status": receipt["status"],
                     "solver_wall_ns": receipt["solver_wall_ns"],
                     "actual_restart_rows": receipt["actual_restart_rows"]}

audit = {
    "status": "PASS_N131_TENPAIR_GAUSS0_RECEIPT_AUDIT",
    "candidate_id": None,
    "same_ordinary_formula": True,
    "same_public_point": True,
    "changed_flag": "--maxnummatrices=0",
    "results": results,
    "sha256": {"source": sha(HERE / "audit.py"),
               "protocol": sha(HERE / "protocol.json"),
               "control_receipt": sha(HERE / "control_result.json"),
               "ordinary_receipt": sha(HERE / "ordinary_result.json"),
               "parent_query": sha(PARENT / "query_result.json")},
}
(HERE / "audit_result.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(audit["status"], results)
