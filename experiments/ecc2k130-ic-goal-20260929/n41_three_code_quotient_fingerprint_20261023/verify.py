"""Replay immutable identity, coverage, and independent audit receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


all_boxes = {}
for folder, expected_boxes, expected_rejected, expected_roots in (
    (HERE, 8, 7, 512), (HERE / "holdout", 16, 15, 1024)
):
    protocol = json.loads((folder / "protocol.json").read_text())
    result = json.loads((folder / "result.json").read_text())
    audit = json.loads((folder / "audit_result.json").read_text())
    assert all(sha(source["path"]) == source["sha256"]
               for source in protocol["sources"].values())
    assert protocol["candidate_id"] is None and result["candidate_id"] is None
    assert result["protocol_sha256"] == sha(folder / "protocol.json")
    assert audit["protocol_sha256"] == result["protocol_sha256"]
    assert audit["result_sha256"] == sha(folder / "result.json")
    assert result["status"] == "PASS_N41_THREE_CODE_QUOTIENT_FINGERPRINT"
    assert audit["status"] == "PASS_INDEPENDENT_SAGE_THREE_CODE_QUOTIENT_AUDIT"
    assert (result["boxes"], result["rejected_boxes"], audit["roots_checked"]) == (
        expected_boxes, expected_rejected, expected_roots)
    assert result["families_covered"] == 8 * expected_boxes
    assert result["wall_seconds"] < protocol["wall_cap_seconds"]
    assert result["self_maxrss_raw"] < protocol["rss_cap_bytes"]
    assert audit["self_maxrss_raw"] < protocol["rss_cap_bytes"]
    assert audit["norm_zeros"] == audit["witness_box_norm_zeros"] == 1
    for row in result["rows"]:
        prefix = tuple(row["prefix"])
        assert len(row["code_triples"]) == 8
        if prefix in all_boxes:
            assert prefix == (38, 53, 16)
            assert all_boxes[prefix] == row["target_rejected"]
        all_boxes[prefix] = row["target_rejected"]
    assert sum(row["target_rejected"] for row in result["rows"]) == expected_rejected

geometry = json.loads((HERE / "geometry_audit_result.json").read_text())
assert geometry["status"] == "PASS_DIRECT_THIRD_PAIR_GEOMETRY"
assert geometry["source_sha256"] == sha(HERE / "audit_geometry_sage.py")
assert geometry["result_sha256"] == sha(HERE / "result.json")
assert geometry["roots_checked"] == 512
assert geometry["matches"][0]["code_triple"] == [24, 37, 10]
assert "depends on axioms: [propext]" in (HERE / "lean_check.log").read_text()
assert len(all_boxes) == 23 and sum(all_boxes.values()) == 22
print(json.dumps({"status": "PASS_THREE_CODE_QUOTIENT_RECEIPTS",
                  "unique_boxes": len(all_boxes), "rejected_boxes": sum(all_boxes.values()),
                  "unique_families": 8 * len(all_boxes)}, sort_keys=True))
