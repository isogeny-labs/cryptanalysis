"""Check the finite W18 source-conflict census and shielded formula delta."""

import hashlib
import json
from math import comb
from pathlib import Path

import shield

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n131_w18_ninepair_orbit_20261012"
BASE = HERE.parent / "n131_fixed_seed_ninepair_cubic_20261011"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    frozen = shield.orbit9.protocol()
    assert frozen["source_sha256"]["source_shield"] == sha(HERE / "shield.py")
    assert frozen["public_target"] == json.loads((PARENT / "protocol.json").read_text())["public_target"]
    assert frozen["target_choice_count"] == 524
    conflicts = shield.source_conflicts()
    assert len(conflicts) == 65
    columns = {int(mask): int(column) for mask, column in
               (line.split() for line in shield.orbit9.base.SUPPORT.read_text().splitlines())}
    code_columns = {}
    for code in shield.orbit9.base.source_domain()[0]:
        left = shield.orbit9.base.pair.mask_from_code(code)
        right = left ^ shield.orbit9.base.pair.SEED
        pair = frozenset((columns[left], columns[right]))
        assert len(pair) == 2
        code_columns[code] = pair
    for first, second in conflicts:
        assert first != second and code_columns[first] & code_columns[second]
    incident = {}
    for code, pair in code_columns.items():
        for column in pair:
            incident.setdefault(column, []).append(code)
    independent_conflicts = {tuple(sorted((first, second)))
                             for codes in incident.values()
                             for i, first in enumerate(codes)
                             for second in codes[i+1:]}
    assert independent_conflicts == set(conflicts)
    census = json.loads((BASE / "support_result.json").read_text())
    row = next(row for row in census["rows"] if row["label"] == "n131_w18_seed212")
    assert comb(len(code_columns), 2) - int(row["matching_coefficients_k0_to_k9"][2]) == 65
    fixture = json.loads((BASE / "control_fixture.json").read_text())
    fixture_codes = [shield.orbit9.base.pair.selector_code(item["masks"][0])
                     for item in fixture["selected"]]
    assert len(fixture_codes) == len(set(fixture_codes)) == 9
    assert len(set.union(*(set(code_columns[code]) for code in fixture_codes))) == 18

    control = json.loads((HERE / "control_result.json").read_text())
    baseline = json.loads((PARENT / "control_result.json").read_text())
    assert control["status"] == baseline["status"] == "PASS_FULL_N131_NINEPAIR_ORBIT_CONSTRUCTED_WITNESS"
    assert control["protocol_sha256"] == sha(HERE / "protocol.json")
    assert control["formula"]["xcnf_sha256"] == sha(HERE / "control.xcnf")
    assert control["assignment_check"]["clauses"] == control["formula"]["clauses"]
    assert control["assignment_check"]["native_xor_rows"] == control["formula"]["native_xor_rows"]
    slot_pairs = comb(9, 2)
    expected_new_clauses = slot_pairs * (1 + 2*len(conflicts))
    expected_new_xors = slot_pairs * 17
    assert control["formula"]["and_gates"] == baseline["formula"]["and_gates"]
    assert control["formula"]["clauses"] - baseline["formula"]["clauses"] == expected_new_clauses
    assert control["formula"]["native_xor_rows"] - baseline["formula"]["native_xor_rows"] == expected_new_xors
    assert control["formula"]["variables"] - baseline["formula"]["variables"] == expected_new_xors
    result = {"status": "PASS_EXACT_N131_NINEPAIR_SOURCE_SHIELD",
              "candidate_id": None, "source_codes": len(code_columns),
              "conflicting_unequal_code_pairs": len(conflicts),
              "slot_pairs": slot_pairs,
              "new_clauses": expected_new_clauses,
              "new_xor_rows": expected_new_xors,
              "new_and_gates": 0,
              "constructed_source_columns_distinct": 18,
              "sha256": {"audit": sha(Path(__file__)),
                         "shield": sha(HERE / "shield.py"),
                         "protocol": sha(HERE / "protocol.json"),
                         "control": sha(HERE / "control_result.json"),
                         "control_formula": sha(HERE / "control.xcnf"),
                         "baseline_control": sha(PARENT / "control_result.json"),
                         "source_census": sha(BASE / "support_result.json"),
                         "support": sha(shield.orbit9.base.SUPPORT)}}
    with (HERE / "shield_audit_result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(result["status"], expected_new_clauses, expected_new_xors)


if __name__ == "__main__":
    main()
