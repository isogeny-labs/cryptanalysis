"""Check frozen identities, exact replay receipts, and accounting boundaries."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


protocol = load("protocol.json")
result = load("result.json")
audit = load("audit_result.json")
traversal_protocol = load("traversal_protocol.json")
traversal = load("traversal_result.json")
target_table = load("target_table.json")
bridge_protocol = load("n131_bridge_protocol_v2.json")
bridge = load("n131_h_bridge_result_v2.json")
bridge_audit = load("n131_h_bridge_audit.json")
bridge_failure = load("n131_bridge_attempt1_failure.json")
for frozen in (protocol, traversal_protocol):
    assert all(sha(source["path"]) == source["sha256"]
               for source in frozen["sources"].values())
    assert frozen["candidate_id"] is None and frozen["worker_count"] == 1
    assert frozen["rss_cap_bytes"] == 4 * 1024**3
assert result["status"] == "PASS_N41_FOUR_CODE_SUFFIX_QUOTIENT"
assert result["protocol_sha256"] == audit["protocol_sha256"] == sha(HERE / "protocol.json")
assert audit["result_sha256"] == sha(HERE / "result.json")
assert audit["status"] == "PASS_INDEPENDENT_SAGE_FOUR_CODE_QUOTIENT_AUDIT"
assert target_table["status"] == "PASS_N41_FOURTH_PAIR_TARGET_TABLE"
assert len(target_table["rows"]) == 40 and all(len(row) == 4 for row in target_table["rows"])
assert protocol["eligible_quads"] == traversal_protocol["eligible_quads"] == 1386816
assert protocol["complete_boxes"] == 5040
assert result["boxes"] == 2 and result["families_covered"] == 32
assert result["rejected_boxes"] == 1 and result["rows"][0]["target_rejected"]
assert not result["rows"][1]["target_rejected"]
assert audit["families_checked"] == 32 and audit["roots_checked"] == 256
assert audit["norm_zeros"] == 1 and audit["target_charts_checked"] == 160
assert audit["zero_locations"][0]["code_quad"] == [24, 37, 10, 0]
assert result["wall_seconds"] < protocol["wall_cap_seconds"]
assert audit["wall_seconds"] < protocol["wall_cap_seconds"]
assert max(result["self_maxrss_raw"], audit["self_maxrss_raw"]) < protocol["rss_cap_bytes"]
assert traversal["status"] == "PASS_N41_FULL_FOUR_AXIS_TRAVERSAL"
assert traversal["protocol_sha256"] == sha(HERE / "traversal_protocol.json")
assert traversal["eligible_quads"] == 1386816
assert traversal["eligible_triples"] == 42432
assert traversal["first_two_state_sums"] == 24864
assert traversal["first_three_state_sums"] == 2715648
assert len(traversal["matches"]) == 1
assert traversal["matches"][0]["state_ids"] == [97, 151, 42, 0, 14, 109, 51]
assert traversal["matches"][0]["code_quad"] == [24, 37, 10, 0]
assert traversal["wall_seconds"] < traversal_protocol["wall_cap_seconds"]
assert traversal["self_maxrss_raw"] < traversal_protocol["rss_cap_bytes"]
assert abs(traversal["wall_seconds"] - sum(traversal[k] for k in
           ("setup_seconds", "query_seconds", "traversal_seconds"))) < 1e-5
assert "depends on axioms: [propext, Quot.sound]" in (HERE / "lean_check.log").read_text()
assert all(sha(source["path"]) == source["sha256"]
           for source in bridge_protocol["sources"].values())
assert bridge_failure["status"] == "PRODUCER_FAILURE_TYPE_ERROR"
assert bridge_failure["exit_code"] == 1
assert bridge_failure["producer_sha256"] == sha(HERE / "n131_h_bridge_sage.py")
assert bridge_failure["stderr_sha256"] == sha(HERE / "n131_bridge_attempt1.stderr.txt")
assert bridge["status"] == "PASS_N131_W23_FIRST_TWO_RESULTANT_BRIDGE"
assert bridge["protocol_sha256"] == sha(HERE / "n131_bridge_protocol_v2.json")
assert bridge_audit["status"] == "PASS_INDEPENDENT_N131_W23_RESULTANT_REPLAY"
assert bridge_audit["result_sha256"] == sha(HERE / "n131_h_bridge_result_v2.json")
assert bridge_audit["auditor_sha256"] == sha(HERE / "audit_n131_h.py")
assert bridge_audit["field_source_sha256"] == sha(
    "/Volumes/SSD990/crypto/research/sat_factor_base_review_20260908/autolab_orbit_extract_20260924/independent_replay.py")
assert bridge["term_count"] == 138 and bridge["degree_z"] == 8
assert bridge["wall_seconds"] < bridge_protocol["wall_cap_seconds"]
assert bridge["self_maxrss_raw"] < bridge_protocol["rss_cap_bytes"]
print(json.dumps({"status": "PASS_FOUR_AXIS_N41_RECEIPTS",
                  "quotient_boxes": result["boxes"],
                  "full_traversal_quads": traversal["eligible_quads"],
                  "verified_matches": len(traversal["matches"]),
                  "n131_bridge_terms": bridge["term_count"]}, sort_keys=True))
