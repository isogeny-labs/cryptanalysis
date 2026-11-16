"""Verify frozen fixed-curve admission evidence and Lean receipt."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    audit = json.loads((HERE / "audit.json").read_text())
    inputs = (("input_selection_result_sha256", "input_sha256",
               PARENT / "xedni-large-order-admission-20261115" / "result.json"),
              ("rank_one_control_result_sha256", "control_sha256",
               PARENT / "xedni-rank-one-coordinate-control-20261115" / "result.json"),
              ("finite_group_source_sha256", "group_source_sha256",
               PARENT / "xedni-public-coordinate-lift-20261115" / "run.py"))
    for protocol_key, result_key, path in inputs:
        assert protocol[protocol_key] == result[result_key] == sha(path)
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["source_sha256"] == sha(HERE / "run.py")
    assert result["status"] == audit["status"] == "PASS"
    assert audit["fields"] == len(result["fields"]) == 8
    assert result["totals"] == {key: audit[key] for key in result["totals"]}
    assert result["totals"] == {"queries": 1471112,
                                "admitted_full_pair_support": 592,
                                "admitted_distinct_nonidentity_pairs": 404}
    assert sum(f["subgroup_order"] for f in result["fields"]) == 3318
    assert sum(f["admitted_offset_count"] for f in result["fields"]) == 68
    for f in result["fields"]:
        q, n = f["subgroup_order"], f["admitted_offset_count"]
        assert len(f["admitted_offsets"]) == n
        assert f["admitted_full_pair_support"] == n * n <= 81
        assert f["admitted_distinct_nonidentity_pairs"] == (n - 1) * (n - 2)
        assert sum(f["counts"].values()) == q * q
        assert f["counts"]["admitted"] == f["admitted_distinct_nonidentity_pairs"]
        assert sha(HERE / f["raw_path"]) == f["raw_sha256"]
    assert not (HERE / "run.stderr").read_text()
    assert not (HERE / "audit.stderr").read_text()
    assert (HERE / "sage-runtime-info.json").is_file()
    formal = HERE / "formal"
    assert (formal / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.35.0-rc4"
    assert "021c46bdd042f67b538b9f9871d556a93713a9a9" in (formal / "lake-manifest.json").read_text()
    lean = (formal / "SelectedAdmission.lean").read_text()
    assert not re.search(r"\b(?:sorry|admit|sorryAx|native_decide)\b", lean)
    build = (formal / "build-output.txt").read_text()
    assert "Build completed successfully" in build
    assert "'XedniFixedCurveAdmission.selected_pair_capacity' depends on axioms: [propext, Classical.choice, Quot.sound]" in build
    seal = HERE / "SEAL.sha256"
    if seal.exists():
        for line in seal.read_text().splitlines():
            expected, rel = line.split("  ", 1)
            assert sha(HERE / rel) == expected, rel
    print(json.dumps({"status": "PASS", "fields": 8,
                      "queries": audit["queries"],
                      "admitted_pairs": audit["admitted_full_pair_support"],
                      "checked_theorems": 1}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
