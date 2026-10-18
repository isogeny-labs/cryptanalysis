"""Read-only checks of the frozen build and bounded query receipts."""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
result = json.loads((HERE / "result.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol["sources"].items():
    assert sha(path) == expected, path
assert result["status"] == "PASS_N41_GUARDED_FUNCTIONAL_LAST_CODE_BUILD"
assert result["candidate_id"] is None
assert result["protocol_sha256"] == sha(HERE / "protocol.json")
assert result["formula_sha256"] == sha(HERE / "formula.xcnf")
assert result["source_positive_count"] == 284
assert sum(result["root_choice_counts"].values()) == 284
assert result["extension_assignments_checked"] == 16
assert result["total_seconds"] < protocol["wall_cap_seconds"]
assert result["self_maxrss_bytes"] < protocol["rss_cap_bytes"]
assert math.isclose(sum(result["phase_seconds"].values()), result["total_seconds"], rel_tol=1e-12)
base = json.loads((Path(protocol["base_formula"]).parent / "build_result.json").read_text())
# Every added non-primary variable is one AND or one native-XOR gate.
assert result["variables"] - base["variables"] == (
    1 + result["extension_and_gates"] + result["extension_native_xor_rows"])
header = (HERE / "formula.xcnf").open().readline().split()
assert header == ["p", "cnf", str(result["variables"]),
                  str(base["clauses"] + base["native_xor_rows"] +
                      result["extension_clauses"] + result["extension_native_xor_rows"])]
assert (HERE / "build.stderr").stat().st_size == 0

audit_path = HERE / "audit_result.json"
if audit_path.exists():
    audit_protocol = json.loads((HERE / "audit_protocol.json").read_text())
    audit = json.loads(audit_path.read_text())
    for path, expected in audit_protocol["sources"].items():
        assert sha(path) == expected, path
    assert audit["audit_protocol_sha256"] == sha(HERE / "audit_protocol.json")
    assert audit["status"] == "PASS_SAGE_GUARDED_ROOT_REPLAY"
    assert audit["positive_rows_checked"] == 284
    assert audit["uniform_rows_checked"] == 1024
    assert audit["reachable_rows_checked"] == 256
    assert audit["root_choice_counts"] == result["root_choice_counts"]

query_path = HERE / "query_result.json"
if query_path.exists():
    query_protocol = json.loads((HERE / "query_protocol.json").read_text())
    query = json.loads(query_path.read_text())
    for path, expected in query_protocol["sources"].items():
        assert sha(path) == expected, path
    assert query["protocol_sha256"] == sha(HERE / "query_protocol.json")
    assert query["solver_stdout_sha256"] == sha(HERE / "solver.stdout")
    assert query["solver_stderr_sha256"] == sha(HERE / "solver.stderr")
    assert query["status"] in {"BOUNDED_UNKNOWN", "SAT_MODEL_UNVERIFIED",
                               "UNSAT_UNVERIFIED", "MONITOR_FAILURE", "RSS_CAP",
                               "PRODUCER_FAILURE_NO_TERMINAL_STATUS"}
    assert query["query_parent_wall_seconds"] <= query_protocol["parent_wall_cap_seconds"] + 2
    assert query["sampled_peak_combined_rss_bytes"] <= query_protocol["rss_cap_bytes"]
    print("PASS_GUARDED_DECODER_RECEIPT", query["status"])
else:
    print("PASS_GUARDED_DECODER_BUILD_RECEIPT")
