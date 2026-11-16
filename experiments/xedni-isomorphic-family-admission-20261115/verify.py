"""Verify pinned model-family results, Sage audit, Lean build, and seal."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "xedni-fixed-curve-admission-20261115"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    audit = json.loads((HERE / "audit.json").read_text())
    parent = json.loads((PARENT / "result.json").read_text())
    assert protocol["parent_fixed_curve_result_sha256"] == result["parent_result_sha256"] == sha(PARENT / "result.json")
    assert protocol["parent_selected_pair_theorem_sha256"] == result["parent_theorem_sha256"] == sha(PARENT / "formal" / "SelectedAdmission.lean")
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["source_sha256"] == sha(HERE / "run.py")
    assert result["status"] == audit["status"] == "PASS"
    assert len(result["fields"]) == audit["fields"] == 8
    assert result["totals"] == {"queries": 1471112, "model_constructions": 32,
                                "candidate_pair_tests": 5884448,
                                "union_admitted_pairs": 592,
                                "new_pairs_from_extra_models": 0}
    for field, old in zip(result["fields"], parent["fields"]):
        p, q = field["field_prime"], field["subgroup_order"]
        assert p == old["field_prime"] and q == old["subgroup_order"]
        assert field["candidate_pair_tests"] == 4*q*q
        assert field["model_constructions"] == len(field["models"]) == 4
        assert field["union_admitted_pairs"] == old["admitted_full_pair_support"]
        assert field["single_model_admitted_pairs"] == old["admitted_full_pair_support"]
        assert field["new_pairs_from_extra_models"] == 0
        assert sha(HERE / field["raw_path"]) == field["raw_sha256"]
        for j, model in enumerate(field["models"]):
            a = j*p
            assert model["j"] == j and model["shift_a"] == a
            assert model["coefficients"] == [0,-3*a,0,3*a*a-1,-a*a*a+a-2]
            assert [c%p for c in model["coefficients"]] == [0,0,0,(-1)%p,(-2)%p]
            assert model["generator"] == [2+a,2]
            assert model["bounded_image_offsets"] == old["admitted_offsets"]
    for key in ("queries", "model_constructions", "candidate_pair_tests", "union_admitted_pairs"):
        assert audit[key] == result["totals"][key]
    assert not (HERE / "run.stderr").read_text()
    assert not (HERE / "audit.stderr").read_text()
    assert (HERE / "sage-runtime-info.json").is_file()
    formal = HERE / "formal"
    assert (formal / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.35.0-rc4"
    assert "021c46bdd042f67b538b9f9871d556a93713a9a9" in (formal / "lake-manifest.json").read_text()
    lean = (formal / "FamilyAdmission.lean").read_text()
    assert not re.search(r"\b(?:sorry|admit|sorryAx|native_decide)\b", lean)
    build = (formal / "build-output.txt").read_text()
    assert "Build completed successfully (3138 jobs)" in build
    for name in ("family_pair_capacity", "translated_polynomial",
                 "translated_coefficients_reduce", "multiple_shift_reduces"):
        assert f"'XedniFamilyAdmission.{name}' depends on axioms:" in build
    assert "sorryAx" not in build
    seal = HERE / "SEAL.sha256"
    if seal.exists():
        for line in seal.read_text().splitlines():
            expected, rel = line.split("  ", 1)
            assert sha(HERE / rel) == expected, rel
    print(json.dumps({"status": "PASS", "fields": 8,
                      "queries": audit["queries"],
                      "candidate_pair_tests": audit["candidate_pair_tests"],
                      "union_admitted_pairs": audit["union_admitted_pairs"],
                      "checked_theorems": 4}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
