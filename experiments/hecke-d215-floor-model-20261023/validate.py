"""Independent integer replay of the four signed floor certificates."""
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "hecke-regular-branch-second-class-20261023"


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = read(HERE / "protocol.json")
    data = read(SOURCE / "data/exp11_class_walk_D215_f6.json")
    audit = read(SOURCE / "audit.json")
    exact = read(SOURCE / "exact_rank.json")
    action = read(HERE / "class_action.json")
    structure = read(HERE / "floor_structure.json")
    generated = read(HERE / "formal/generation.json")
    for name, digest in protocol["source_sha256"].items():
        assert sha(SOURCE / name) == digest, name
    assert action["norm_form_orders"]["norm2_f3"] == 14
    assert action["class_numbers"]["3"] == 28
    assert structure["status"] == "VERIFIED_FOUR_SIGNED_FLOOR_DIRECTIONS"
    assert structure["component_sizes"] == [14, 14, 14, 14]
    floor = {r["column"] for r in audit["point_records"] if r["endomorphism_conductor"] == 6}
    assert len(floor) == 56
    supports = []
    used_rows = Counter()
    for cert in structure["certificates"]:
        replay = Counter()
        for encoded, sign in cert["rows"].items():
            row_index = int(encoded)
            assert sign in (-1, 1)
            assert audit["row_records"][row_index]["degree"] == 2
            assert audit["row_records"][row_index]["source_conductor"] == 3
            used_rows[row_index] += 1
            for col, value in data["relation_rows"][row_index].items():
                replay[int(col)] += sign * int(value)
        replay = {col: value for col, value in replay.items() if value}
        recorded = {int(col): int(value) for col, value in cert["floor_vector"].items()}
        assert replay == recorded and set(recorded) <= floor
        assert len(recorded) == 14 and set(recorded.values()) <= {-1, 1}
        supports.append(set(recorded))
    assert len(used_rows) == 56 and set(used_rows.values()) == {1}
    assert len(set.union(*supports)) == sum(map(len, supports)) == len(floor)
    assert exact["ranks"]["regularized"]["full_QQ"] - exact["ranks"]["regularized"]["nonfloor_QQ"] == 4
    assert generated["floor_structure_sha256"] == sha(HERE / "floor_structure.json")
    assert generated["generated_sha256"] == sha(HERE / "formal/FloorKernel.lean")
    check = (HERE / "formal/floor-kernel-check.txt").read_text()
    assert "concrete_certificates_independent" in check and "sorryAx" not in check
    result = {"status": "PASS_FOUR_FLOOR_CERTIFICATES_REPLAY",
              "protocol_sha256": sha(HERE / "protocol.json"),
              "source_matrix_sha256": sha(SOURCE / "data/exp11_class_walk_D215_f6.json"),
              "class_action_sha256": sha(HERE / "class_action.json"),
              "structure_sha256": sha(HERE / "floor_structure.json"),
              "lean_generation_sha256": sha(HERE / "formal/generation.json"),
              "lean_check_sha256": sha(HERE / "formal/floor-kernel-check.txt"),
              "signed_row_count": len(used_rows), "covered_floor_columns": len(floor),
              "floor_kernel_dimension": 4, "candidate_id": None, "timing_claim": None}
    (HERE / "validation.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
