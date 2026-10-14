"""Audit exact sign fibers and source-code labels for the N41 seven-pair table."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    protocol = read(HERE / "protocol.json")
    assert protocol["status"] == "FROZEN"
    for path, expected in protocol["sources"].items():
        assert sha(Path(path)) == expected, path
    geometry = read(Path(protocol["geometry_path"]))
    assert geometry["curve_id"] == protocol["curve_id"]
    assert geometry["positive_control"]["subgroup_target"] == protocol["public_point"]
    assert geometry["positive_control"]["raw_target"] == protocol["raw_target"]
    seed = geometry["fixed_seed_sum_code"]
    bits = [i for i in range(8) if i != seed.bit_length() - 1]
    assert len(bits) == 7
    columns = {int(k): int(v) for k, v in geometry["mask_columns"].items()}
    permitted = set(geometry["permitted_canonical_a"])
    code_mask = {}
    slot_rows = []
    for slot, block in enumerate(geometry["blocks"]):
        by_code = defaultdict(lambda: defaultdict(list))
        for state in block["states"]:
            a, b = state["a"], state["b"]
            assert a in permitted and b == a ^ seed
            code = sum(((a >> bit) & 1) << j for j, bit in enumerate(bits))
            if code in code_mask:
                assert code_mask[code] == a
            else:
                code_mask[code] = a
            wanted = {columns[a], columns[b]}
            assert set(state["columns"]) == wanted
            x, y = state["raw_sum"]
            assert x != 0
            by_code[code][x].append(y)
        assert len(by_code) == 40 and len(block["states"]) == 160
        for roots in by_code.values():
            assert len(roots) == 2
            for x, ys in roots.items():
                assert len(ys) == 2 and len(set(ys)) == 2
                assert ys[0] ^ ys[1] == x
        slot_rows.append({"slot": slot, "rotation": geometry["rotations"][slot],
                          "codes": len(by_code), "coordinate_roots": sum(map(len, by_code.values())),
                          "signed_raw_points": len(block["states"]),
                          "sign_fibers_checked": sum(map(len, by_code.values()))})
    assert len(code_mask) == 40
    assert len(set(code_mask.values())) == 40
    assert all((code_mask[c] in permitted) for c in code_mask)
    conflict_pairs = []
    for a_code, a in code_mask.items():
        a_cols = {columns[a], columns[a ^ seed]}
        for b_code, b in code_mask.items():
            b_cols = {columns[b], columns[b ^ seed]}
            if a_cols & b_cols:
                conflict_pairs.append([a_code, b_code])
    conflict_pairs.sort()
    pair_count = len(conflict_pairs)
    assert pair_count > 0
    slot_pair_count = len(slot_rows) * (len(slot_rows) - 1) // 2
    out = {
        "status": "PASS_N41_W8_SIGN_AND_LABEL_CLOSURE",
        "curve_id": geometry["curve_id"],
        "public_point": protocol["public_point"],
        "raw_target": protocol["raw_target"],
        "fixed_seed_sum_code": seed,
        "code_bits": bits,
        "permitted_codes": len(code_mask),
        "slots": slot_rows,
        "ordered_conflicting_code_pairs_per_slot_pair": pair_count,
        "slot_pairs": slot_pair_count,
        "total_cross_slot_conflict_clauses": pair_count * slot_pair_count,
        "conflict_pairs_sha256": hashlib.sha256(json.dumps(conflict_pairs, separators=(",", ":")).encode()).hexdigest(),
    }
    with (HERE / "result.json").open("x") as stream:
        json.dump(out, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(out["status"], out["total_cross_slot_conflict_clauses"])


if __name__ == "__main__":
    main()
