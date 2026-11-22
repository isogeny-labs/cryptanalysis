"""Read-only source, proof, build, and bounded-query receipt checks."""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


for name in ("protocol.json", "bdd_protocol.json", "audit_protocol.json",
             "build_protocol.json", "query_protocol.json", "order_protocol.json"):
    protocol = load(name)
    for path,expected in protocol["sources"].items():
        assert sha(path) == expected, (name,path)

source_protocol = load("protocol.json")
source = load("result.json")
bdd_protocol = load("bdd_protocol.json")
bdd = load("bdd_result.json")
audit_protocol = load("audit_protocol.json")
audit = load("audit_result.json")
build_protocol = load("build_protocol.json")
build = load("build_result.json")
assert source["status"] == "PASS_N41_TARGET_JOINT_RESIDUAL_SCREEN"
assert source["candidate_id"] is None
assert source["protocol_sha256"] == sha(HERE / "protocol.json")
assert source["support_sha256"] == sha(HERE / "support.json")
assert source["controls_sha256"] == sha(HERE / "controls.json")
assert source["raw_pairs"] == 284**2
assert source["usable_signed_pairs"] == source["distinct_w_z_pairs"] == 79424
assert source["raw_pairs"] == (source["column_collision_pairs"]+
       source["identity_pairs"]+source["zero_x_pairs"]+source["usable_signed_pairs"])
assert source["reachable_controls"] == 2048
assert source["total_seconds"] < source_protocol["wall_cap_seconds"]
assert source["self_maxrss_bytes"] < source_protocol["rss_cap_bytes"]
assert math.isclose(sum(source["phase_seconds"].values()),source["total_seconds"],rel_tol=1e-12)
assert bdd["status"] == "PASS_JOINT_PREFIX_BDD_SCREEN"
assert bdd["protocol_sha256"] == sha(HERE / "bdd_protocol.json")
assert bdd["total_seconds"] < bdd_protocol["wall_cap_seconds"]
assert bdd["self_maxrss_bytes"] < bdd_protocol["rss_cap_bytes"]
row16 = next(row for row in bdd["rows"] if row["prefix_bits"] == 16)
assert row16["support_words"] == 79262 and row16["bdd_nodes"] == 100081
order_protocol = load("order_protocol.json")
order = load("order_result.json")
assert order["status"] == "PASS_BDD_ORDER_SCREEN"
assert order["protocol_sha256"] == sha(HERE / "order_protocol.json")
assert order["total_seconds"] < order_protocol["wall_cap_seconds"]
assert order["self_maxrss_bytes"] < order_protocol["rss_cap_bytes"]
assert {row["order"]:row["bdd_nodes"] for row in order["rows"]} == {
       "w_first":100081,"z_first":112012,"interleaved":312982}
assert audit["status"] == "PASS_SAGE_FULL_JOINT_RESIDUAL_REPLAY"
assert audit["protocol_sha256"] == sha(HERE / "audit_protocol.json")
assert audit["support_rows_checked"] == source["usable_signed_pairs"]
assert audit["reachable_controls_checked"] == source["reachable_controls"]
assert audit["reachable_prefix_hits"] == source["reachable_prefix_hits"]
assert audit["total_seconds"] < audit_protocol["wall_cap_seconds"]
assert audit["self_maxrss_bytes"] < audit_protocol["rss_cap_bytes"]
first_audit = load("audit_protocol_attempt1.json")
assert sha(HERE / "audit_sage_attempt1.py") == first_audit["sources"][str(HERE / "audit_sage.py")]
assert b"TimeoutError: frozen independent Sage joint-support audit cap" in (
       HERE / "audit_attempt1.stderr").read_bytes()
assert build["status"] == "PASS_N41_JOINT_PREFIX16_BDD_BUILD"
assert build["protocol_sha256"] == sha(HERE / "build_protocol.json")
assert build["formula_sha256"] == sha(HERE / "formula.xcnf")
assert build["bdd_nodes"] == row16["bdd_nodes"]
assert build["support_rows_accepted"] == source["usable_signed_pairs"]
assert build["reachable_control_passes"] == source["reachable_prefix_hits"]["16"]
assert build["total_seconds"] < build_protocol["wall_cap_seconds"]
assert build["self_maxrss_bytes"] < build_protocol["rss_cap_bytes"]
assert math.isclose(sum(build["phase_seconds"].values()),build["total_seconds"],rel_tol=1e-12)
assert (HERE / "formula.xcnf").open().readline().strip() == (
       f"p cnf {build['variables']} {build['constraints']}")
assert (HERE / "run.stderr").stat().st_size == 0
assert (HERE / "bdd.stderr").stat().st_size == 0
assert (HERE / "audit.stderr").stat().st_size == 0
assert (HERE / "build.stderr").stat().st_size == 0
assert (HERE / "order.stderr").stat().st_size == 0
assert (HERE / "lean.stderr").stat().st_size == 0
lean_output = (HERE / "lean.stdout").read_text()
assert lean_output.count("does not depend on any axioms") == 3
assert b"error:" in (HERE / "lean_attempt1.stdout").read_bytes()

if (HERE / "query_result.json").exists():
    query_protocol = load("query_protocol.json")
    query = load("query_result.json")
    assert query["protocol_sha256"] == sha(HERE / "query_protocol.json")
    assert query["solver_stdout_sha256"] == sha(HERE / "solver.stdout")
    assert query["solver_stderr_sha256"] == sha(HERE / "solver.stderr")
    assert query["query_parent_wall_seconds"] <= query_protocol["parent_wall_cap_seconds"]+2
    assert query["sampled_peak_combined_rss_bytes"] <= query_protocol["rss_cap_bytes"]
    assert query["status"] in {"BOUNDED_UNKNOWN","SAT_MODEL_UNVERIFIED",
                                "UNSAT_UNVERIFIED","RSS_CAP","MONITOR_FAILURE",
                                "PRODUCER_FAILURE_NO_TERMINAL_STATUS"}
    print("PASS_JOINT_PREFIX_RECEIPT",query["status"])
else:
    print("PASS_JOINT_PREFIX_BUILD_RECEIPT")
