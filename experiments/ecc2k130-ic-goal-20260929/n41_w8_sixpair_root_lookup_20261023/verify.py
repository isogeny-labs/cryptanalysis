"""Read-only audit of the failed first build and corrected bounded control."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda name: json.loads((HERE / name).read_text())

failed = read("build_failure_v1.json")
assert failed["status"] == "PRODUCER_FAILURE_COORDINATE_MISMATCH"
assert failed["exit_code"] == 1
assert failed["protocol_sha256"] == sha(HERE / "build_protocol.json")
assert failed["builder_sha256"] == sha(HERE / "build.py")
assert failed["circuit_sha256"] == sha(HERE / "circuit.py")
for stem in ("build", "build_v2", "query", "source_sign_audit"):
    protocol_name = {"build": "build_protocol.json",
                     "build_v2": "build_protocol_v2.json",
                     "query": "query_protocol.json",
                     "source_sign_audit": "source_sign_audit_protocol.json"}[stem]
    protocol = read(protocol_name)
    for name, item in protocol["sources"].items():
        assert sha(item["path"]) == item["sha256"], (stem, name)

build = read("build_result_v2.json")
query = read("query_result.json")
assert build["status"] == "PASS_N41_ROOT_LOOKUP_CIRCUIT_V2"
assert build["protocol_sha256"] == sha(HERE / "build_protocol_v2.json")
assert build["formula_sha256"] == sha(HERE / "n41_public_root_lookup_v2.xcnf")
assert build["formula_bytes"] == (HERE / "n41_public_root_lookup_v2.xcnf").stat().st_size
assert build["counts"]["source_edges_per_slot"] == 40
assert build["counts"]["cross_slot_column_conflicts"] == 690
assert build["positive_assignment_check"] == {
    "clauses": build["counts"]["clauses"],
    "native_xor_rows": build["counts"]["native_xor_rows"],
}
assert len(set(build["witness_edges"])) == 6
assert query["status"] == "BOUNDED_UNKNOWN"
assert query["solver_terminal_indeterminate"] is True
assert query["solver_terminal_sat"] is False
assert query["solver_terminal_unsat"] is False
assert query["solver_exit_code"] == 0
assert query["stop_reason"] is None
assert query["public_point"] == build["public_point"]
assert query["protocol_sha256"] == sha(HERE / "query_protocol.json")
assert query["solver_stdout_sha256"] == sha(HERE / "query.stdout")
assert query["solver_stderr_sha256"] == sha(HERE / "query.stderr")
assert read("query_protocol.json")["worker_count"] == 1
assert read("query_protocol.json")["rss_cap_bytes"] == 4294967296
signs = read("source_sign_audit_result.json")
assert signs["status"] == "PASS_N41_SOURCE_ROOT_SIGN_AUDIT"
assert signs["state_count"] == 960 and signs["root_sign_pairs"] == 480
assert signs["protocol_sha256"] == sha(HERE / "source_sign_audit_protocol.json")
proof = (HERE / "TreeLift.lean").read_text()
lean_log = (HERE / "lean_check.log").read_text()
assert (HERE / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.34.1"
assert not re.search(r"^\s*(sorry|admit)(?:\s|$)", proof, re.MULTILINE)
assert "error:" not in lean_log and "sorryAx" not in lean_log
for theorem in ("signed_neg", "link_lift", "six_leaf_lift"):
    assert f"'TreeLift.{theorem}' depends on axioms: [propext]" in lean_log
print("PASS_N41_ROOT_LOOKUP_ARCHIVE")
