"""Read-only verification of frozen source bindings and three-code receipts."""
import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load(name):
    return json.loads((HERE / name).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def protocol(name):
    record = load(name)
    for path, digest in record["sources"].items():
        assert sha(path) == digest, (name, path)
    assert record["candidate_id"] is None
    assert record["worker_count"] == 1
    assert record["wall_cap_seconds"] == 180
    assert record["rss_cap_bytes"] == 4294967296
    return record


def main():
    p = protocol("protocol.json")
    a = protocol("audit_protocol.json")
    runtime = load("sage_runtime_info.json")
    assert runtime["status"] == "verified"
    result = load("result.json")
    audit = load("audit_result.json")
    transfer = load("transfer_result.json")
    geo = json.loads((ROOT / "n41_w8_fixed_sum_table_20261009" / "geometry.json").read_text())
    ordinary = json.loads((ROOT / "n41_w8_fixedseed_ordinary_join_20261013" / "audit_result.json").read_text())

    assert result["status"] == "PASS_N41_THREE_CODE_TARGET_GATE"
    assert audit["status"] == "PASS_INDEPENDENT_SAGE_THREE_CODE_TARGET_GATE"
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert audit["protocol_sha256"] == sha(HERE / "audit_protocol.json")
    assert result["curve_id"] == p["curve_id"] == geo["curve_id"]
    assert result["candidate_id"] is audit["candidate_id"] is None
    assert result["families"] == 1554
    assert result["panel_count"] == audit["panels_checked"] == 33
    assert result["random_suffix_count"] == p["random_suffix_count"] == 32
    assert result["peak_process_rss_sample_bytes"] < p["rss_cap_bytes"]
    assert audit["peak_process_rss_sample_bytes"] < a["rss_cap_bytes"]
    assert result["wall_ns"] < p["wall_cap_seconds"] * 10**9
    assert audit["wall_ns"] < a["wall_cap_seconds"] * 10**9
    assert sum(result["phase_ns"].values()) <= result["wall_ns"]
    assert audit["admissible_code_triples_checked"] == result["total_admissible_code_triples"] == 1323474
    assert audit["coordinate_membership_slots_checked"] == 4 * result["total_admissible_code_triples"] == 5293896
    assert audit["affine_candidates"] == result["total_affine_candidates"] == 1
    assert audit["exact_coordinate_candidates"] == result["total_exact_coordinate_candidates"] == 1
    assert audit["full_point_matches"] == result["total_full_point_matches"] == 1
    assert (HERE / "audit.stdout").read_text().strip() == "PASS_INDEPENDENT_SAGE_THREE_CODE_TARGET_GATE 5293896 1"
    assert not (HERE / "audit.stderr").read_text()

    panels = result["panels"]
    witness_ids = [row["state_id"] for row in ordinary["states"]]
    assert panels[0] == {"kind": "witness", "suffix_state_ids": witness_ids[3:],
                         "admissible_code_triples": 38874,
                         "affine_candidates": [[24, 37, 10, [2]]],
                         "exact_coordinate_candidates": [[24, 37, 10, [2]]],
                         "full_point_matches": [witness_ids[:3]]}
    rng = random.Random(p["suffix_seed"])
    expected = [witness_ids[3:]]
    while len(expected) <= p["random_suffix_count"]:
        ids = [rng.randrange(160) for _ in range(4)]
        cols = [col for k, sid in enumerate(ids, 3)
                for col in geo["blocks"][k]["states"][sid]["columns"]]
        if len(set(cols)) == 8:
            expected.append(ids)
    assert [row["suffix_state_ids"] for row in panels] == expected
    assert all(row["kind"] == "random" and not row["affine_candidates"]
               and not row["exact_coordinate_candidates"] and not row["full_point_matches"]
               for row in panels[1:])
    assert sum(row["admissible_code_triples"] for row in panels) == result["total_admissible_code_triples"]

    count_source = ROOT / "n131_w20_sevenpair_gate_20261010" / "count_result_v2.json"
    assert transfer["status"] == "PASS_LITERAL_W20_THREE_CODE_GATE_PROJECTION"
    assert transfer["source_sha256"] == sha(count_source)
    code_count = json.loads(count_source.read_text())["selected_valid_unordered_pairs_per_slot"]
    assert transfer["valid_codes_per_slot"] == code_count == 132045
    triples = code_count**3
    assert int(transfer["ordered_code_pairs"]) == code_count**2
    assert int(transfer["ordered_code_triples"]) == triples
    assert int(transfer["triple_checks_per_second_for_600s_exhaustion"]) == (triples + 599) // 600
    assert int(transfer["single_bit_per_triple_bytes"]) == (triples + 7) // 8
    assert int(transfer["eight_131_bit_pair_coordinates_bytes"]) == code_count**2 * 8 * 17
    print("PASS_N41_THREE_CODE_RECEIPT_VERIFICATION", len(panels), triples)


if __name__ == "__main__":
    main()
