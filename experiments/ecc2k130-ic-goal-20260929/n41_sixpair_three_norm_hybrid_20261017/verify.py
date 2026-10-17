"""Read back source bindings, independent controls, Lean, and solver status."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
read = lambda name: json.loads((D / name).read_text())

protocol = read("protocol.json")
assert sha(D / "circuit.py") == protocol["circuit_sha256"]
assert sha(D / "build.py") == protocol["builder_sha256"]
assert sha(D / "sage_runtime_info.json") == protocol["runtime_info_sha256"]
assert sha(D / "build_v1_failure.json") == protocol["previous_failure_sha256"]
assert all(sha(ROOT / path) == digest for path, digest in protocol["sources"].items())
failure = read("build_v1_failure.json")
assert failure["status"] == "PRODUCER_FAILURE"
assert failure["builder_sha256"] == sha(D / "build_v1.py")
assert failure["protocol_sha256"] == sha(D / "protocol_v1.json")
assert failure["stdout_sha256"] == sha(D / "build_v1.stdout")
assert failure["stderr_sha256"] == sha(D / "build_v1.stderr")
build = read("build_result.json")
assert build["status"] == "PASS_UNPINNED_THREE_NORM_HYBRID_BUILD"
assert build["protocol_sha256"] == sha(D / "protocol.json")
assert build["formula_sha256"] == sha(D / "public.xcnf")
assert (D / "build.stderr").read_bytes() == b""

for protocol_name, result_name, expected in (
    ("audit_protocol.json", "audit_result.json", "PASS_INDEPENDENT_SAGE_THREE_NORM_HYBRID_CONTROL"),
    ("source_audit_protocol.json", "source_audit_result.json", "PASS_SAGE_ALL_N41_SOURCE_QUADRATICS_AND_EIGHT_NORMS"),
    ("formula_audit_protocol.json", "formula_audit_result.json", "PASS_HYBRID_XCNF_BYTE_REBUILD_AND_FREE_CODES"),
):
    p = read(protocol_name)
    assert all(sha(path) == digest for path, digest in p["sources"].items())
    if "runtime_info_sha256" in p:
        assert p["runtime_info_sha256"] == sha(D / "sage_runtime_info.json")
    result = read(result_name)
    assert result["status"] == expected
    assert result["protocol_sha256"] == sha(D / protocol_name)
assert read("audit_result.json")["build_sha256"] == sha(D / "build_result.json")
assert read("formula_audit_result.json")["formula_sha256"] == sha(D / "public.xcnf")
formula_failure = read("formula_audit_v1_failure.json")
assert formula_failure["status"] == "PRODUCER_FAILURE"
assert formula_failure["source_sha256"] == sha(D / "audit_formula_v1.py")
assert formula_failure["protocol_sha256"] == sha(D / "formula_audit_protocol_v1.json")
assert read("formula_audit_protocol.json")["previous_failure_sha256"] == sha(D / "formula_audit_v1_failure.json")
assert read("source_audit_result.json")["quadratic_roots_checked"] == 240
assert len(read("source_audit_result.json")["records"]) == 8
lean = (D / "lean.stdout").read_text()
assert (D / "lean.stderr").read_bytes() == b""
assert "'HybridStructure.two_triples_are_six_sum' depends on axioms: [propext]" in lean
assert "'HybridStructure.orient_target' depends on axioms: [propext]" in lean
assert not any(word in (D / "HybridStructure.lean").read_text()
               for word in ("sorry", "admit", "sorryAx"))

query_protocol = read("query_protocol.json")
assert query_protocol["runner_sha256"] == sha(D / "query.py")
assert query_protocol["solver_sha256"] == sha(query_protocol["solver_path"])
assert all(sha(D / name) == digest for name, digest in query_protocol["sources"].items())
assert query_protocol["worker_count"] == 1
assert query_protocol["parent_wall_cap_s"] == 600
assert query_protocol["rss_cap_bytes"] == 4 * (1 << 30)
query = read("query_result.json")
assert query["query_protocol_sha256"] == sha(D / "query_protocol.json")
assert query["stdout_sha256"] == sha(D / "solver.stdout")
assert query["stderr_sha256"] == sha(D / "solver.stderr")
assert not query["monitor_degraded"]
assert query["sampled_peak_combined_rss_bytes"] < query_protocol["rss_cap_bytes"]
if query["status"] == "BOUNDED_UNKNOWN":
    assert query["stop_reason"] in ("PARENT_WALL_CAP", None)
    assert "s SATISFIABLE" not in query["terminal_lines"]
    assert "s UNSATISFIABLE" not in query["terminal_lines"]
elif query["status"] == "SAT_PENDING_REPLAY":
    assert "s SATISFIABLE" in query["terminal_lines"]
else:
    assert query["status"] in ("UNSAT_UNCERTIFIED", "PRODUCER_FAILURE")
out = {"status": "PASS_BOUND_HYBRID_QUERY_RECEIPT",
       "candidate_id": None, "query_status": query["status"],
       "formula_sha256": sha(D / "public.xcnf"),
       "query_sha256": sha(D / "query_result.json"),
       "independent_sage_audits": 2}
(D / "terminal.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(out["status"], out["query_status"])
