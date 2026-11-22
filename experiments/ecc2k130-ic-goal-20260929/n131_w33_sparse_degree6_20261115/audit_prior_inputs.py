"""Replay exact W33 equation-support identity across the two sparse reducers."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n41_n131_sparse_block_macaulay_20261019"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_prior(path, target_index):
    lines = path.read_text().splitlines()
    assert lines[0] == "EQS 34 131 4 2"
    assert len(lines) == 132
    rows = []
    for coordinate, line in enumerate(lines[1:]):
        values = [int(value) for value in line.split()]
        assert values[0] == coordinate
        count, masks = values[1], values[2:]
        assert count == len(masks) == len(set(masks))
        rows.append(set(masks))
    assert target_index in (0, 1)
    return rows


def parse_current(path, target_index):
    lines = path.read_text().splitlines()
    assert lines[0] == f"W33 34 131 1619 {target_index}"
    assert len(lines) == 132
    rows = []
    for line in lines[1:]:
        values = [int(value) for value in line.split()]
        count, masks = values[0], values[1:]
        assert count == len(masks) == len(set(masks))
        rows.append(set(masks))
    return rows


def canonical_digest(rows):
    data = json.dumps([sorted(row) for row in rows], separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def main():
    prior_receipt = json.loads((PRIOR / "prepare_result.json").read_text())
    current_receipt = json.loads((HERE / "prepare_result.json").read_text())
    output = []
    for target_index in (0, 1):
        old_path = PRIOR / f"n131_t{target_index}_a0.eqs"
        new_path = HERE / f"equations_{target_index}.txt"
        old_hash, new_hash = sha256(old_path), sha256(new_path)
        prior_row = next(row for row in prior_receipt["outputs"]
                         if row["label"] == f"n131_t{target_index}_a0")
        current_row = next(row for row in current_receipt["rows"]
                           if row["target_index"] == target_index)
        assert old_hash == prior_row["sha256"]
        assert new_hash == current_row["equation_sha256"]
        old_rows = parse_prior(old_path, target_index)
        new_rows = parse_current(new_path, target_index)
        assert len(old_rows) == len(new_rows) == 131
        assert all(0 <= mask < (1 << 34) and mask.bit_count() <= 4
                   for row in old_rows + new_rows for mask in row)
        differing = [i for i, (old, new) in enumerate(zip(old_rows, new_rows))
                     if old != new]
        supports = sum(map(len, old_rows))
        assert supports == prior_row["support_entries"]
        assert supports == current_row["coordinate_support_total"]
        assert not differing
        assert canonical_digest(old_rows) == canonical_digest(new_rows)
        output.append({
            "target_index": target_index,
            "coordinates": 131,
            "support_entries": supports,
            "differing_coordinates": differing,
            "canonical_support_sha256": canonical_digest(old_rows),
            "prior_file_sha256": old_hash,
            "current_file_sha256": new_hash,
        })
    print(json.dumps({"status": "MATCH_EXACT_W33_COORDINATE_SUPPORTS",
                      "arms": output}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
