"""Read-only custody and cross-check for the raw-fiber census package."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    v1 = read("protocol.json")
    v2 = read("protocol_v2.json")
    fail = read("census_v1_status.json")
    census = read("census_result.json")
    audit_p = read("audit_protocol.json")
    audit = read("audit_result.json")
    analysis_p = read("analysis_protocol.json")
    analysis = read("analysis_result.json")
    assert v1["status"] == "FROZEN_BEFORE_CENSUS"
    assert sha(HERE / "census_v1.py") == v1["source_sha256"]
    assert fail["status"] == "CAPPED_240_SECONDS"
    assert fail["protocol_sha256"] == sha(HERE / "protocol.json")
    assert fail["stderr_sha256"] == sha(HERE / "census.stderr.txt")
    assert v2["status"] == "FROZEN_AMENDED_BEFORE_CENSUS"
    assert v2["amends_protocol_sha256"] == sha(HERE / "protocol.json")
    assert v2["failed_attempt_status_sha256"] == sha(HERE / "census_v1_status.json")
    assert v2["source_sha256"] == sha(HERE / "census.py")
    for name, digest in v2["input_sha256"].items():
        assert sha(v2["inputs"][name]) == digest
    assert census["status"] == "PASS_EXACT_POSITION_CENSUS"
    assert census["protocol_sha256"] == sha(HERE / "protocol_v2.json")
    assert census["source_raw_x_per_position"] == census["image_raw_x_per_position"] == 4134
    assert census["union_raw_points_per_position"] == 16536
    assert not (HERE / "census_v2.stderr.txt").read_text()
    assert audit_p["status"] == "FROZEN_BEFORE_AUDIT"
    assert audit_p["source_sha256"] == sha(HERE / "audit_sage.py")
    for name, digest in audit_p["input_sha256"].items():
        assert sha(audit_p["inputs"][name]) == digest
    assert audit["status"] == "PASS_ALL_VALID_SELECTORS"
    assert audit["protocol_sha256"] == sha(HERE / "audit_protocol.json")
    assert audit["valid_selectors"] == 4134
    for key in ("ordered_class_pairs_digest", "raw_image_x_digest"):
        assert audit[key] == census[key]
    assert not (HERE / "audit.stderr.txt").read_text()
    assert analysis_p["status"] == "FROZEN_BEFORE_ANALYSIS"
    assert analysis_p["source_sha256"] == sha(HERE / "analyze.py")
    assert analysis_p["census_result_sha256"] == sha(HERE / "census_result.json")
    assert analysis["status"] == "PASS_EXACT_CLASS_COUNTS_WITH_LABELED_SUBGROUP_HEURISTIC"
    assert analysis["protocol_sha256"] == sha(HERE / "analysis_protocol.json")
    source = [census["original_cofactor_classes_per_position"][str(i)] for i in range(4)]
    image = [census["image_cofactor_classes_per_position"][str(i)] for i in range(4)]
    union = [a+b for a, b in zip(source, image)]
    assert source == [2160, 2067, 1974, 2067]
    assert image == [4134, 0, 4134, 0]
    assert union == [6294, 2067, 6108, 2067]
    for policy, counts in (("original", source), ("image", image), ("union", union)):
        for m in (9, 10):
            row = analysis["rows"][f"{policy}_m{m}"]
            assert row["per_position_classes"] == counts
            assert sum(int(v) for v in row["ordered_tuples_by_target_cofactor_class"]) == sum(counts)**m
    lean_text = (HERE / "CofactorImage.lean").read_text()
    assert all(word not in lean_text for word in ("sorry", "admit", "sorryAx"))
    lean_output = (HERE / "lean.stdout").read_text()
    assert "projected_image_doubles' does not depend on any axioms" in lean_output
    assert "image_class_even' depends on axioms: [propext]" in lean_output
    assert not (HERE / "lean.stderr").read_text()
    print(json.dumps({"status": "PASS", "valid_selectors": 4134,
                      "union_raw_points_per_position": 16536,
                      "independent_sage_replay": "PASS_ALL_VALID_SELECTORS",
                      "lean_axioms": ["none", "propext"]}, sort_keys=True))


if __name__ == "__main__":
    main()
