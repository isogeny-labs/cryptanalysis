"""Independent readback of frozen family resultants and Sage group audit."""
import hashlib
import importlib.util
import json
from pathlib import Path


D = Path(__file__).resolve().parent
ROOT = D.parent
PRIOR = ROOT / "n41_rr_two_slot_quotient_20261016"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    p = read(D / "protocol.json")
    rp = read(D / "run_protocol.json")
    receipt = read(D / "run_receipt.json")
    result = read(D / "result.json")
    assert p["schema"] == 1 and p["candidate_id"] is None
    assert sha(D / "freeze.py") == p["producer_sha256"]
    assert sha(D / "run.py") == p["runner_sha256"]
    assert sha(D / "run_monitored.py") == p["monitor_sha256"] == rp["monitor_sha256"]
    assert sha(D / "sage_runtime_info.json") == p["runtime_info_sha256"] == rp["runtime_info_sha256"]
    assert sha(D / "protocol.json") == rp["protocol_sha256"] == receipt["protocol_sha256"] == result["protocol_sha256"]
    assert sha(D / "run_protocol.json") == receipt["run_protocol_sha256"]
    assert sha(D / "result.json") == receipt["result_sha256"]
    assert sha(D / "run.stdout") == receipt["stdout_sha256"]
    assert sha(D / "run.stderr") == receipt["stderr_sha256"]
    assert receipt["status"] == "PRODUCER_COMPLETED" and receipt["exit_code"] == 0
    assert receipt["stop_reason"] is None and (D / "run.stderr").read_text() == ""
    assert receipt["parent_wall_s"] < p["wall_cap_s"]
    assert receipt["sampled_peak_combined_rss_bytes"] < p["rss_cap_bytes"]
    for relative, digest in p["sources"].items():
        assert sha(ROOT / relative) == digest, relative
    assert result["status"] == "COMPLETE_N41_RR_FAMILY_RESULTANT"
    assert result["family_count"] == [36, 36]
    assert result["family_pairs"] == 1296
    assert result["candidate_state_combinations_after_family_filter"] == 16

    spec = importlib.util.spec_from_file_location("rr_verifier_field", PRIOR / "run.py")
    rr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rr)
    g = read(rr.GEOMETRY)
    fixed = [g["blocks"][slot]["states"][sid]
             for slot, sid in zip(range(2, 6), p["fixed_state_ids"])]
    qx, qy = p["raw_target"]
    basis, _, _ = rr.kernel([rr.row(s["raw_sum"]) for s in fixed] +
                            [rr.row([qx, qy ^ qx])])
    fixed_cols = {c for s in fixed for c in s["columns"]}
    keys = []
    ids_by_code = []
    rank_two = []
    for slot in (0, 1):
        by_code = {}
        key_by_id = {}
        for state_id, state in enumerate(g["blocks"][slot]["states"]):
            if fixed_cols.intersection(state["columns"]):
                continue
            a, b = rr.signature(state["raw_sum"], basis)
            assert b != 0
            key_by_id[state_id] = rr.F.mul(a, rr.inv(b))
            by_code.setdefault(state["a"], []).append(state_id)
        assert len(by_code) == 36 and all(len(x) == 4 for x in by_code.values())
        rank_two.append(sum(len({key_by_id[i] for i in ids}) > 1
                            for ids in by_code.values()))
        keys.append(key_by_id)
        ids_by_code.append(by_code)
    assert rank_two == result["linear_span_rank_two_families"] == [36, 36]
    assert result["linear_span_rejected_pairs"] == 0
    for slot in (0, 1):
        assert len(result["family_polynomials"][slot]) == 36
        for code, ids in ids_by_code[slot].items():
            coefficients = result["family_polynomials"][slot][str(code)]
            assert len(coefficients) == 5 and coefficients[-1] == 1
            for state_id in ids:
                x = keys[slot][state_id]
                value = 0
                for coefficient in reversed(coefficients):
                    value = rr.F.mul(value, x) ^ coefficient
                assert value == 0
    compatible = []
    state_matches = []
    for code_a, ids_a in sorted(ids_by_code[0].items()):
        values_a = {keys[0][i] for i in ids_a}
        for code_b, ids_b in sorted(ids_by_code[1].items()):
            values_b = {keys[1][j] for j in ids_b}
            if values_a.isdisjoint(values_b):
                continue
            compatible.append([code_a, code_b])
            for i in ids_a:
                for j in ids_b:
                    if keys[0][i] == keys[1][j] and not (
                        set(g["blocks"][0]["states"][i]["columns"]) &
                        set(g["blocks"][1]["states"][j]["columns"])
                    ):
                        state_matches.append([i, j])
    assert compatible == result["compatible_family_pairs"] == [[6, 196]]
    assert 1296 - len(compatible) == result["nonzero_resultant_pairs"] == 1295
    assert state_matches == result["exact_state_pairs"] == [[12, 122]]
    prior = read(PRIOR / "result.json")
    sage = read(PRIOR / "audit_sage.json")
    assert sha(PRIOR / "result.json") == sage["runner_result_sha256"]
    assert sage["status"] == "PASS" and sage["group_pairs_checked"] == 20736
    assert sage["distinct_column_group_matches"] == state_matches
    assert prior["matches"] == state_matches
    assert (D / "lean_build.exit").read_text().strip() == "0"
    assert (D / "lean_build.stderr").read_text() == ""
    log = (D / "lean_build.stdout").read_text()
    assert "FamilyResultant.familyProduct_zero_iff_common" in log
    assert "[propext, Quot.sound]" in log
    assert not any(token in (D / "FamilyResultant.lean").read_text()
                   for token in ("sorry", "admit", "sorryAx"))
    audit = {"status": "PASS_FAMILY_RESULTANT_AUDIT",
             "eligible_families": [36, 36], "family_pairs": 1296,
             "linear_span_rank_two_families": rank_two,
             "exact_compatible_family_pairs": compatible,
             "independently_replayed_state_pairs": state_matches,
             "group_pairs_in_prior_sage_audit": sage["group_pairs_checked"]}
    (D / "verification.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    w23_path = ROOT / "n131_w23_sixpair_density_20261016" / "audit_result.json"
    w23 = read(w23_path)
    assert w23["status"] == "PASS_INDEPENDENT_W23_EDGE_CENSUS"
    edges = w23["worker_result"]["usable_edges"]
    assert edges == 1049218
    projection = {"status": "EXPLICIT_PAIRWISE_FAMILY_FRONTIER",
                  "n131_audit_sha256": sha(w23_path),
                  "usable_edges_per_slot": edges,
                  "two_free_slot_family_pairs_per_fixed_suffix": edges * edges,
                  "quartic_evaluations_per_fixed_suffix": 4 * edges * edges,
                  "minimum_quartic_evaluations_per_second_for_600s":
                      (4 * edges * edges + 599) // 600,
                  "four_slot_signed_suffix_assignments": (4 * edges) ** 4}
    (D / "projection.json").write_text(json.dumps(projection, sort_keys=True, indent=2) + "\n")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
