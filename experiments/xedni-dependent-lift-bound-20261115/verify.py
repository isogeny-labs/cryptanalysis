"""Verify the dependent-lift formalization's source and build receipt."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FORMAL = HERE / "formal"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = json.loads((HERE / "SOURCE.json").read_text())
    assert source["schema"] == "xedni-dependent-lift-source-v1"
    base_bytes = (FORMAL / "XedniObstruction.lean").read_bytes()
    assert sha(FORMAL / "XedniObstruction.lean") == source["base_source_sha256"]
    blob = hashlib.sha1(b"blob " + str(len(base_bytes)).encode() + b"\0" + base_bytes).hexdigest()
    assert blob == source["base_git_blob"]
    assert (FORMAL / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.35.0-rc4"
    manifest = json.loads((FORMAL / "lake-manifest.json").read_text())
    assert "021c46bdd042f67b538b9f9871d556a93713a9a9" in json.dumps(manifest)
    assert "021c46bdd042f67b538b9f9871d556a93713a9a9" in (FORMAL / "lakefile.toml").read_text()
    code = (FORMAL / "XedniDependentLift.lean").read_text()
    assert not any(token in code for token in ("sorry", "admit", "sorryAx", "native_decide"))
    assert "axiom " not in code
    output = (FORMAL / "build-output.txt").read_text()
    assert "Build completed successfully" in output
    assert "sorryAx" not in output
    declaration = "'XedniObstruction.dependent_lift_sample_count' depends on axioms: "
    line = next(row for row in output.splitlines() if declaration in row)
    assert line.endswith("[propext, Classical.choice, Quot.sound]")
    assert output.count("depends on axioms:") == 15
    print(json.dumps({"status": "PASS", "checked_declarations": 15,
                      "base_source_sha256": source["base_source_sha256"],
                      "extension_source_sha256": sha(FORMAL / "XedniDependentLift.lean")},
                     sort_keys=True))


if __name__ == "__main__":
    main()
