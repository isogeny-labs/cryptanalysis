"""Read-only receipt and source-binding check for the N41 two-code study."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_protocol(name):
    record = read(name)
    for path, digest in record.get("sources", {}).items():
        assert sha(path) == digest, (name, path)
    return sha(HERE / name)


def xor_all(values):
    out = 0
    for value in values:
        out ^= value
    return out


def main():
    runtime = read("sage_runtime_info.json")
    assert runtime["status"] == "verified"
    for name in ("protocol.json", "audit_protocol.json", "target_protocol_v2.json",
                 "target_audit_protocol.json", "cubic_protocol.json"):
        check_protocol(name)

    census = read("result.json")
    audit = read("audit_result.json")
    cubic = read("cubic_result.json")
    target = read("target_result_v2.json")
    target_audit = read("target_audit_result.json")
    transfer = read("transfer_result.json")
    cases_path = HERE / "cases.jsonl"
    cases = [json.loads(line) for line in cases_path.read_text().splitlines()]

    assert census["status"] == "PASS_EXACT_N41_TWO_CODE_AFFINE_SPAN_CENSUS"
    assert audit["status"] == "PASS_INDEPENDENT_SAGE_TWO_CODE_AFFINE_SPANS"
    assert census["cases_sha256"] == audit["cases_sha256"] == cubic["cases_sha256"] == sha(cases_path)
    assert len(cases) == census["family_pairs_checked"] == audit["families_checked"] == 1554
    assert census["column_conflict_pairs"] + len(cases) == 40 * 40
    assert audit["raw_group_sums_checked"] == len(cases) * 16
    assert census["histogram"] == {"column_conflict": 46, "x_count_8": 1554,
                                   "x_rank_7": 1554, "z_count_8": 1554,
                                   "z_rank_7": 1554}
    assert len({(row["left_code"], row["right_code"]) for row in cases}) == 1554
    for row in cases:
        assert row["raw_state_combinations"] == 16
        assert row["x_affine_rank"] == row["reciprocal_affine_rank"] == 7
        assert len(set(row["x_coordinates"])) == len(set(row["reciprocal_coordinates"])) == 8
        assert xor_all(row["x_coordinates"]) and xor_all(row["reciprocal_coordinates"])

    assert cubic["status"] == "PASS_NONZERO_CUBIC_COEFFICIENT_ALL_TWO_CODE_FAMILIES"
    assert cubic["families_checked"] == 1554
    assert cubic["x_zero_cubic_coefficients"] == cubic["reciprocal_zero_cubic_coefficients"] == 0
    assert cubic["distinct_x_cubic_coefficients"] == cubic["distinct_reciprocal_cubic_coefficients"] == 1554
    assert target["status"] == "PASS_N41_TARGET_CONDITIONED_TWO_CODE_SPAN_SCREEN"
    assert target_audit["status"] == "PASS_INDEPENDENT_SAGE_TARGET_SPAN_SCREEN"
    assert target["panel_size"] == target_audit["panels_checked"] == 65
    assert target["random_suffix_count"] == 64
    assert target["suffix_residual_affine_rank"] == target_audit["random_suffix_affine_rank"] == 41
    assert target["total_exact_family_hits"] == target_audit["total_exact_hits"] == 1
    assert target["total_affine_family_hits"] == target_audit["total_affine_hits"] == 1
    assert target_audit["family_membership_checks"] == 65 * 1554
    assert target["panels"][0]["kind"] == "witness"
    assert target["panels"][0]["exact_code_pairs"] == target["panels"][0]["affine_code_pairs"] == [[24, 37]]
    assert all(not p["exact_code_pairs"] and not p["affine_code_pairs"]
               for p in target["panels"][1:])
    assert read("target_failure_v1.json")["status"] == "PRODUCER_FAILURE"
    assert read("failure_diagnosis_v1.json")["status"] == "DIAGNOSED_PRODUCER_ASSERTION_BUG"

    assert transfer["status"] == "PASS_LITERAL_W20_TWO_CODE_TABLE_PROJECTION"
    assert transfer["source_sha256"] == sha(HERE.parent / "n131_w20_sevenpair_gate_20261010" / "count_result_v2.json")
    assert int(transfer["ordered_code_pairs"]) == transfer["valid_codes_per_slot"] ** 2
    assert int(transfer["code_pairs_per_second_for_600s_exhaustion"]) == (int(transfer["ordered_code_pairs"]) + 599) // 600
    assert int(transfer["bytes_for_eight_131_bit_coordinates_per_pair"]) == int(transfer["ordered_code_pairs"]) * 8 * 17
    assert int(transfer["bytes_for_one_bit_per_pair"]) == (int(transfer["ordered_code_pairs"]) + 7) // 8

    source = (HERE / "CubicParity.lean").read_text()
    assert all(token not in source for token in ("sorry", "admit", "sorryAx", "axiom "))
    assert (HERE / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.34.1"
    lean_log = (HERE / "cubic_lean_check.log").read_text()
    for theorem in ("cubicCoeff_of_differences", "nonzero_cubic_of_independent_differences",
                    "cubic_of_sevenIndependent"):
        assert f"CubicParity.{theorem}' depends on axioms: [propext, Quot.sound]" in lean_log
    affine_log = (HERE / "lean_check.log").read_text()
    assert "AffineSpan.no_additional_affine_parity' depends on axioms: [propext, Quot.sound]" in affine_log
    print("PASS_N41_TWO_CODE_RECEIPT_VERIFICATION", len(cases), target_audit["family_membership_checks"])


if __name__ == "__main__":
    main()
