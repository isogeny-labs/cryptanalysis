"""Serialize the exact six-slot rows and one planted group-sum control."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
GEOMETRY = HERE.parent / "n41_w6_s8_distinct_window_geometry" / "geometry.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def main():
    assert not any((HERE / name).exists() for name in
                   ("ordinary_input.txt", "control_input.txt", "join_input_manifest.json"))
    screen = json.loads((HERE / "result.json").read_text())
    rows = json.loads((HERE / "union_rows.json").read_text())
    geometry = json.loads(GEOMETRY.read_text())
    assert screen["status"] == "PASS_EXACT_GROUP_CENSUS"
    assert sha(HERE / "union_rows.json") == screen["union_rows_sha256"]
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, name="t", modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    control = curve(0)
    lines = []
    for slot, block in enumerate(rows):
        assert block["rotation"] == screen["rotations"][slot]
        source_rows = block["rows"]
        assert len(source_rows) == 64
        ordered = []
        for image_branch in (0, 1):
            for row in source_rows:
                xy = row["image"] if image_branch else row["original"]
                ordered.append([*xy, row["column"], row["mask"],
                                row["sign"], image_branch])
        assert len(ordered) == 128
        lines.append(f"{block['rotation']} 128")
        lines.extend(" ".join(map(str, row)) for row in ordered)
        selected = ordered[64 if slot == 0 else 0]
        control += curve(field.from_integer(selected[0]), field.from_integer(selected[1]))
    assert control != curve(0)
    assert 549756390943*control == curve(0)
    body = "\n".join(lines) + "\n"
    public = geometry["public_target_q"]
    (HERE / "ordinary_input.txt").write_text(
        f"{public[0]} {public[1]} 549756390943 6\n" + body)
    (HERE / "control_input.txt").write_text(
        f"{encode(control[0])} {encode(control[1])} 549756390943 6\n" + body)
    receipt = {"kind": "n41_w6_adjacent_union_join_input_manifest",
               "status": "FROZEN_INPUTS", "candidate_id": None,
               "curve_id": geometry["curve_id"], "workload_id": geometry["workload_id"],
               "rotations": screen["rotations"], "point_count_per_slot": 128,
               "ordinary_target": public,
               "control_target": [encode(control[0]), encode(control[1])],
               "control_row_ids": [64, 0, 0, 0, 0, 0],
               "screen_result_sha256": sha(HERE / "result.json"),
               "union_rows_sha256": sha(HERE / "union_rows.json"),
               "source_sha256": sha(__file__),
               "ordinary_input_sha256": sha(HERE / "ordinary_input.txt"),
               "control_input_sha256": sha(HERE / "control_input.txt")}
    (HERE / "join_input_manifest.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
