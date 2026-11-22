"""Read back frozen sources, monitor, Lean proof, group audit and N131 count."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    p, rp, receipt = (read(D / name) for name in
                      ("protocol.json", "run_protocol.json", "run_receipt.json"))
    result, audit = (read(D / name) for name in ("result.json", "audit_result.json"))
    assert p["candidate_id"] is None and p["schema"] == 1
    assert p["free_slots"] == [0, 1, 2] and p["fixed_state_ids"] == [47, 128, 34]
    assert sha(D / "run.py") == p["runner_sha256"]
    assert sha(D / "sage_runtime_info.json") == p["runtime_info_sha256"] == rp["runtime_info_sha256"]
    assert sha(D / "run_monitored.py") == rp["monitor_sha256"]
    assert sha(D / "protocol.json") == rp["protocol_sha256"] == receipt["protocol_sha256"] == result["protocol_sha256"]
    assert sha(D / "run_protocol.json") == receipt["run_protocol_sha256"]
    for relative, digest in p["sources"].items():
        assert sha(ROOT / relative) == digest, relative
    assert receipt["status"] == "PRODUCER_COMPLETED" and receipt["exit_code"] == 0
    assert receipt["stop_reason"] is None and receipt["parent_wall_s"] < p["wall_cap_s"]
    assert receipt["sampled_peak_combined_rss_bytes"] < p["rss_cap_bytes"]
    assert sha(D / "result.json") == receipt["result_sha256"] == audit["result_sha256"]
    assert sha(D / "run.stdout") == receipt["stdout_sha256"]
    assert sha(D / "run.stderr") == receipt["stderr_sha256"]
    assert (D / "run.stderr").read_text() == (D / "audit.stderr").read_text() == ""
    assert audit["status"] == "PASS_INDEPENDENT_THREE_FAMILY_GROUP_JOIN"
    assert sha(D / "audit_sage.py") == audit["audit_source_sha256"]
    assert audit["protocol_sha256"] == sha(D / "protocol.json")
    assert audit["group_hits"] == audit["determinant_hits"] == result["valid_determinant_zero_states"]
    assert result["family_counts"] == [37, 37, 37]
    assert result["family_triples"] == 37**3
    assert result["determinant_evaluations"] == 64 * result["family_triples"]
    assert result["determinant_zero_family_triples"] == 1
    assert result["determinant_zero_state_triples"] == 1
    assert result["expected_state_triple"] == [12, 122, 116]
    geometry = read(ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json")
    fixed = [geometry["blocks"][slot]["states"][sid]
             for slot, sid in zip((3, 4, 5), p["fixed_state_ids"])]
    fixed_columns = {c for state in fixed for c in state["columns"]}
    fixed_points = {tuple(state["raw_sum"]) for state in fixed}
    qx, qy = p["raw_target"]
    fixed_points.add((qx, qy ^ qx))
    assert len(fixed_points) == 4
    free_points = []
    for slot in range(3):
        values = {tuple(state["raw_sum"]) for state in geometry["blocks"][slot]["states"]
                  if fixed_columns.isdisjoint(state["columns"])}
        assert len(values) == result["state_counts"][slot]
        assert values.isdisjoint(fixed_points)
        free_points.append(values)
    assert all(free_points[i].isdisjoint(free_points[j])
               for i in range(3) for j in range(i + 1, 3))
    assert (D / "lean_build.exit").read_text().strip() == "0"
    assert (D / "lean_build.stderr").read_text() == ""
    proof = (D / "lean_build.stdout").read_text()
    assert "'ThreeFamilyProduct.familyProduct_zero_iff' depends on axioms: [propext, Quot.sound]" in proof
    lean = (D / "ThreeFamilyProduct.lean").read_text()
    assert not any(token in lean for token in ("sorry", "admit", "sorryAx", "native_decide"))
    w23_path = ROOT / "n131_w23_sixpair_density_20261016/audit_result.json"
    w23 = read(w23_path)
    assert w23["status"] == "PASS_INDEPENDENT_W23_EDGE_CENSUS"
    edges = w23["worker_result"]["usable_edges"]
    assert edges == 1049218
    projection = {
        "status": "LITERAL_THREE_FAMILY_EVALUATION_FRONTIER",
        "n131_source_audit_sha256": sha(w23_path),
        "usable_edges_per_slot": edges,
        "three_free_slot_family_triples_per_fixed_suffix": edges**3,
        "determinant_evaluations_per_fixed_suffix": 64 * edges**3,
        "minimum_determinant_evaluations_per_second_for_600s": (64 * edges**3 + 599) // 600,
        "three_slot_signed_suffix_assignments": (4 * edges)**3,
    }
    (D / "projection.json").write_text(json.dumps(projection, sort_keys=True, indent=2) + "\n")
    out = {"status": "PASS_THREE_FAMILY_READBACK",
           "protocol_sha256": sha(D / "protocol.json"),
           "result_sha256": sha(D / "result.json"),
           "audit_result_sha256": sha(D / "audit_result.json"),
           "families_tested": result["family_triples"],
           "group_hits": audit["group_hits"],
           "distinct_evaluation_points_checked": True,
           "lean_axioms": ["propext", "Quot.sound"]}
    (D / "verification.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
