"""Read-only audit of the N41 modular-product panel, search, and transfer gate."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_hashes(protocol_name, mapping):
    p = json.loads((HERE / protocol_name).read_text())
    assert {key: sha(path) for key, path in mapping.items()} == p["sha256"]
    return p


def main():
    parent = GOAL / "n41_symbolic_two_bucket_20261011/run.py"
    runtime = HERE / "sage_runtime_info.json"
    panel_protocol = check_hashes("protocol.json", {
        "runner": HERE / "run.py", "parent": parent,
        "parent_protocol": GOAL / "n41_symbolic_two_bucket_20261011/protocol.json",
        "geometry": GOAL / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json",
        "sage_runtime": runtime})
    panel = json.loads((HERE / "result.json").read_text())
    assert panel["protocol_sha256"] == sha(HERE / "protocol.json")
    assert panel["status"] == "COMPLETE_PANEL" and len(panel["rows"]) == len(panel_protocol["cases"]) == 8
    assert all(row["gcd_degree"] == (1 if row["kind"] == "positive" and
               row["raw_option"] == 3 and row["right_seed"] == 5 else 0)
               for row in panel["rows"])
    assert all(row["reduced_degree"] < row["norm_degree"] for row in panel["rows"])
    global_protocol = check_hashes("global_protocol.json", {
        "runner": HERE / "run_global.py", "parent": parent,
        "panel_protocol": HERE / "protocol.json", "panel_result": HERE / "result.json",
        "sage_runtime": runtime})
    global_result = json.loads((HERE / "global_result.json").read_text())
    assert global_result["protocol_sha256"] == sha(HERE / "global_protocol.json")
    assert global_result["status"] == "COMPLETE_PAIRED_PANEL"
    assert global_result["global_left_degree"] == 4032
    for left, right in zip(panel["rows"], global_result["rows"]):
        assert (left["kind"], left["raw_option"], left["right_seed"], left["gcd_degree"]) == (
            right["kind"], right["raw_option"], right["right_seed"], right["gcd_degree"])
        assert left["modular_product_ns"] == right["panel_modular_product_ns"]
        assert left["gcd_ns"] == right["panel_modular_gcd_ns"]
    search_protocol = check_hashes("search_protocol.json", {
        "runner": HERE / "run_search.py", "parent": parent,
        "panel_protocol": HERE / "protocol.json", "global_result": HERE / "global_result.json",
        "sage_runtime": runtime})
    search = json.loads((HERE / "search_result.json").read_text())
    assert search["protocol_sha256"] == sha(HERE / "search_protocol.json")
    assert search["status"] == "ALGEBRAIC_HIT_PENDING_GROUP_REPLAY"
    assert search["decisions"] == 20 and search["hit"]["right_seed"] == 5
    assert search["hit"]["raw_option"] == 3
    assert search["hit"]["left_families"] == [{"left_seed": 16, "roots": [585190544792]}]
    assert search["whole_wall_ns"] >= sum(search[key] for key in
        ("setup_ns", "global_product_ns", "target_projection_ns", "norm_ns", "gcd_ns", "localize_ns"))
    audit_protocol = check_hashes("audit_protocol.json", {
        "auditor": HERE / "audit_sage.py",
        "earlier_auditor": GOAL / "n41_symbolic_two_bucket_20261011/audit.py",
        "search_protocol": HERE / "search_protocol.json", "search_result": HERE / "search_result.json",
        "geometry": GOAL / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json",
        "prior_witness": GOAL / "n41_seed_sum_s3_bucket_norm_20261010/batch_result.json",
        "sage_runtime": runtime})
    audit = json.loads((HERE / "audit_result.json").read_text())
    assert audit["protocol_sha256"] == sha(HERE / "audit_protocol.json")
    assert audit["status"] == "PASS_INDEPENDENT_GROUP_REPLAY_OF_UNPINNED_RESIDUAL_HIT"
    assert audit["decisions"] == search["decisions"] and audit["hit"] == search["hit"]
    assert audit["projected_pair_witness_match"] is True
    v2_protocol = check_hashes("search_v2_protocol.json", {
        "runner": HERE / "run_search_v2.py", "parent": parent,
        "source_protocol": HERE / "search_protocol.json", "sage_runtime": runtime})
    v2 = json.loads((HERE / "search_v2_result.json").read_text())
    assert v2["protocol_sha256"] == sha(HERE / "search_v2_protocol.json")
    assert v2["status"] == search["status"] and v2["hit"] == search["hit"]
    assert v2["decisions"] == search["decisions"] == 20
    assert v2["positive_gcds_without_base_field_root"] == 0
    assert v2["whole_wall_ns"] >= sum(v2[key] for key in
        ("setup_ns", "global_product_ns", "target_projection_ns", "norm_ns", "gcd_ns", "localize_ns"))
    audit_v2_protocol = check_hashes("audit_v2_protocol.json", {
        "auditor": HERE / "audit_v2_sage.py",
        "search_protocol": HERE / "search_v2_protocol.json",
        "search_result": HERE / "search_v2_result.json",
        "independent_prior_audit": HERE / "audit_result.json",
        "sage_runtime": runtime})
    audit_v2 = json.loads((HERE / "audit_v2_result.json").read_text())
    assert audit_v2["protocol_sha256"] == sha(HERE / "audit_v2_protocol.json")
    assert audit_v2["status"] == "PASS_CHECKED_SAGE_V2_SAME_RESIDUAL_GROUP_REPLAY"
    assert audit_v2["hit"] == v2["hit"]
    projection_protocol = check_hashes("projection_protocol.json", {
        "script": HERE / "projection.py",
        "support": GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv",
        "n41_global": HERE / "global_result.json", "n41_search": HERE / "search_result.json",
        "n41_audit": HERE / "audit_result.json"})
    projection = json.loads((HERE / "projection_result.json").read_text())
    assert projection["protocol_sha256"] == sha(HERE / "projection_protocol.json")
    assert projection["unfiltered_global_polynomial_degree"] == (2**18 - 1) * 2**18
    assert projection["dense_full_field_coefficient_bytes"] == ((projection["unfiltered_global_polynomial_degree"] + 1) * 131 + 7) // 8
    assert projection["literal_seed_fiber_gcd_decisions"] == 4 * (2**18 - 1)
    sparsity_protocol = check_hashes("sparsity_protocol.json", {
        "script": HERE / "sparsity_sage.py", "parent": parent,
        "global_result": HERE / "global_result.json", "sage_runtime": runtime})
    sparsity = json.loads((HERE / "sparsity_result.json").read_text())
    coefficients = json.loads((HERE / "nonzero_coefficients.json").read_text())
    assert sparsity["protocol_sha256"] == sha(HERE / "sparsity_protocol.json")
    assert sparsity["degree"] == 4032 and len(coefficients) == sparsity["nonzero_coefficients"] == 4007
    assert all(0 <= i <= 4032 and 0 < value < 2**41 for i, value in coefficients)
    assert all(coefficients[i][0] < coefficients[i+1][0] for i in range(len(coefficients)-1))
    proof = (HERE / "lean_check.txt").read_text()
    assert "FamilyGate.modular_gate_exact" in proof and "error:" not in proof and "sorryAx" not in proof
    assert (HERE / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.34.1"
    for name in ("stdout.log", "stderr.log", "global_stdout.log", "global_stderr.log",
                 "search_stdout.log", "search_stderr.log", "audit_stdout.log", "audit_stderr.log",
                 "sparsity_stdout.log", "sparsity_stderr.log",
                 "search_v2_stdout.log", "search_v2_stderr.log",
                 "audit_v2_stdout.log", "audit_v2_stderr.log"):
        assert (HERE / name).exists()
    print(json.dumps({"status": "PASS_FROZEN_N41_JOINT_FAMILY_SEARCH_AND_N131_GATE",
                      "panel_rows": len(panel["rows"]), "search_decisions": search["decisions"],
                      "search_wall_seconds": search["whole_wall_ns"] / 1e9,
                      "v2_search_wall_seconds": v2["whole_wall_ns"] / 1e9,
                      "v2_localize_seconds": v2["localize_ns"] / 1e9,
                      "n41_product_nonzero_coefficients": len(coefficients),
                      "n131_dense_bytes": projection["dense_full_field_coefficient_bytes"]},
                     sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
