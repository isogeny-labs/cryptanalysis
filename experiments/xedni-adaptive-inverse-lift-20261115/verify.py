"""Verify the frozen adaptive inverse-lift packet without rerunning the census."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    audit = json.loads((HERE / "audit.json").read_text())
    source = HERE / "run.py"
    inp = PARENT / "xedni-large-order-admission-20261115" / "result.json"
    parent = PARENT / "xedni-public-coordinate-lift-20261115" / "run.py"
    assert protocol["input_selection_result_sha256"] == digest(inp) == result["input_sha256"]
    assert protocol["parent_finite_group_source_sha256"] == digest(parent) == result["parent_source_sha256"]
    assert result["protocol_sha256"] == digest(HERE / "protocol.json")
    assert result["source_sha256"] == digest(source)
    assert result["status"] == audit["status"] == "PASS"
    assert len(result["fields"]) == audit["fields"] == 8
    totals = result["totals"]
    assert totals["queries"] == audit["queries"] == 1471112
    assert totals["public_group_tests"] == audit["public_group_tests"] == 1461174
    assert totals["rational_relations"] == audit["rational_relations"] == 3310
    assert totals["rational_relations"] == totals["curve_constructions"] == totals["public_inverse_pairs"]
    assert totals["status_invalid_curve"] == 0
    assert totals["queries"] == sum(totals[f"status_{s}"] for s in
        ("identity", "duplicate", "public_nonrelation", "rational_relation"))
    shard_count = 0
    row_count = 0
    for field in result["fields"]:
        q = field["subgroup_order"]
        counts = field["counts"]
        assert counts["queries"] == q * q
        assert counts["public_inverse_pairs"] == counts["rational_relations"] == q - 1
        assert field["first_rational_relation"] == {"query_index_one_based": 35, "t": [0, 34]}
        for shard in field["row_shards"]:
            path = HERE / shard["path"]
            assert path.is_file() and digest(path) == shard["sha256"]
            shard_count += 1
            import gzip
            with gzip.open(path, "rt") as rows:
                row_count += sum(1 for _ in rows)
    assert row_count == totals["queries"]
    assert not (HERE / "run.stderr").read_text()
    assert not (HERE / "audit.stderr").read_text()
    assert (HERE / "sage-runtime-info.json").is_file()
    formal = HERE / "formal"
    assert (formal / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.35.0-rc4"
    manifest = json.loads((formal / "lake-manifest.json").read_text())
    assert any(p.get("name") == "mathlib" and
               p.get("rev") == "021c46bdd" + p.get("rev", "")[9:] for p in manifest["packages"])
    lean = (formal / "AdaptiveInverseLift.lean").read_text()
    for forbidden in ("sorry", "admit", "sorryAx", "native_decide"):
        assert forbidden not in lean
    build = (formal / "build-output.txt").read_text()
    assert "Build completed successfully" in build
    for name in ("rational_model", "inverse_relation", "reduction_model"):
        assert f"'{ 'XedniAdaptiveInverseLift.' + name }' depends on axioms:" in build
    assert "[propext, Classical.choice, Quot.sound]" in build
    assert "[propext, Quot.sound]" in build
    print(json.dumps({"status": "PASS", "queries": row_count,
                      "shards": shard_count, "rational_relations": totals["rational_relations"],
                      "lean_build": "PASS"}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
