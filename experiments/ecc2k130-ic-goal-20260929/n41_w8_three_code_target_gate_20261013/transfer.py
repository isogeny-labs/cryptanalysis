"""Literal W20 enumeration and storage projection for this three-code gate."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n131_w20_sevenpair_gate_20261010" / "count_result_v2.json"


def main():
    source = json.loads(SOURCE.read_text())
    p = source["selected_valid_unordered_pairs_per_slot"]
    assert p == 132045
    pair_count = p * p
    triple_count = pair_count * p
    result = {
        "status": "PASS_LITERAL_W20_THREE_CODE_GATE_PROJECTION",
        "candidate_id": None,
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "valid_codes_per_slot": p,
        "ordered_code_pairs": str(pair_count),
        "ordered_code_triples": str(triple_count),
        "triple_checks_per_second_for_600s_exhaustion": str((triple_count + 599) // 600),
        "single_bit_per_triple_bytes": str((triple_count + 7) // 8),
        "eight_131_bit_pair_coordinates_bytes": str(pair_count * 8 * 17),
        "scope": "literal enumeration and uncompressed coordinate table; cross-slot exclusions, implicit constraints and N131 affine ranks unmeasured",
    }
    target = HERE / "transfer_result.json"
    if target.exists():
        assert json.loads(target.read_text()) == result
    else:
        target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(result["status"], result["ordered_code_triples"])


if __name__ == "__main__":
    main()
