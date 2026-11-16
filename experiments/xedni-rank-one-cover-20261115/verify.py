"""Independent arithmetic and receipt audit for the rank-one cover packet."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    inp = PARENT / "xedni-large-order-admission-20261115" / "result.json"
    ctl = PARENT / "xedni-rank-one-coordinate-control-20261115" / "result.json"
    assert protocol["selected_fields_result_sha256"] == result["input_sha256"] == sha(inp)
    assert protocol["rank_one_control_result_sha256"] == result["control_sha256"] == sha(ctl)
    assert result["source_sha256"] == sha(HERE / "run.py")
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["status"] == "PASS"
    selected = [x for x in json.loads(inp.read_text())["rows"] if x["selected"]]
    controls = {x["field_prime"]: x for x in json.loads(ctl.read_text())["rows"]}
    assert len(selected) == len(result["rows"]) == 8
    par = protocol["parameters"]
    assert par == {"L": 4, "c": 1, "K": 4, "T": 1, "lift_arity": 2}
    assert result["parameters"] == par
    for source, row in zip(selected, result["rows"]):
        p, q = source["field_prime"], source["subgroup_order"]
        assert row["field_prime"] == p and row["subgroup_order"] == q
        assert row["witness_box"] == (4 * 4 + 1) ** 2 - 1 == 288
        assert row["rank_gap_left"] == 1 * (2 * 1 + 1) == 3
        assert row["allowed_coordinate_radius"] == 4
        assert row["cover_capacity"] == 1 * (2 * 4 + 1) == 9
        assert row["uncovered_residues_at_least"] == q - 9 > 0
        assert row["measured_centered_sum_radius"] == controls[p]["two_point_sum_coordinate_radius_K"]
        assert row["measured_exceeds_allowed"] == (row["measured_centered_sum_radius"] > 4)
    assert not (HERE / "run.stderr").read_text()
    formal = HERE / "formal"
    assert (formal / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.35.0-rc4"
    assert "021c46bdd042f67b538b9f9871d556a93713a9a9" in (formal / "lake-manifest.json").read_text()
    lean = (formal / "RankOneCover.lean").read_text()
    assert not any(token in lean for token in ("sorry", "admit", "sorryAx", "native_decide"))
    build = (formal / "build-output.txt").read_text()
    assert "Build completed successfully (3138 jobs)" in build
    for theorem in ("coordinate_cover_lower_bound", "torsion_coordinate_cover_lower_bound",
                    "no_uniform_rank_one_cover", "no_uniform_rank_one_cover_with_torsion"):
        assert f"'XedniRankOneCover.{theorem}' depends on axioms: [propext, Classical.choice, Quot.sound]" in build
    seal = HERE / "SEAL.sha256"
    if seal.exists():
        for line in seal.read_text().splitlines():
            expected, rel = line.split("  ", 1)
            assert sha(HERE / rel) == expected, rel
    print(json.dumps({"status": "PASS", "fields": len(selected),
                      "minimum_uncovered": min(x["uncovered_residues_at_least"] for x in result["rows"]),
                      "checked_theorems": 4}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
