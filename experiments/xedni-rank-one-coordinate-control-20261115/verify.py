"""Verify rank-one control sources, arithmetic receipt, and Lean proof."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "xedni-large-order-admission-20261115" / "result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    audit = json.loads((HERE / "audit.json").read_text())
    assert result["status"] == audit["status"] == "PASS"
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["source_sha256"] == sha(HERE / "run.py")
    assert result["input_sha256"] == sha(INPUT) == \
        protocol["input_selection_result_sha256"]
    assert result["sage_runtime_sha256"] == sha(HERE / "sage-runtime-info.json")
    assert audit["offsets_checked"] == sum(x["subgroup_order"] for x in result["rows"])
    assert not (HERE / "run.stderr").read_bytes()
    assert not (HERE / "audit.stderr").read_bytes()
    assert (HERE / "lean-toolchain").read_text().strip() == \
        "leanprover/lean4:v4.35.0-rc4"
    manifest = (HERE / "lake-manifest.json").read_text()
    assert "021c46bdd042f67b538b9f9871d556a93713a9a9" in manifest
    assert "021c46bdd042f67b538b9f9871d556a93713a9a9" in \
        (HERE / "lakefile.toml").read_text()
    code = (HERE / "RankOneCoordinate.lean").read_text()
    assert not any(x in code for x in ("sorry", "admit", "sorryAx", "native_decide"))
    assert "axiom " not in code
    build = (HERE / "build-output.txt").read_text()
    assert "Build completed successfully" in build
    assert "sorryAx" not in build
    assert "'XedniRankOneCoordinate.no_rank_gap_at_centered_slope' depends on axioms: " \
        "[propext, Classical.choice, Quot.sound]" in build
    assert build.count("depends on axioms:") == 1
    print(json.dumps({"schema": "xedni-rank-one-coordinate-verify-v1",
                      "status": "PASS", "checked_declarations": 1,
                      "control_fields": len(result["rows"]),
                      "offsets_checked": audit["offsets_checked"]},
                     sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
