"""Check the pinned Lean build, axiom audit and file seal."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    formal = HERE / "formal"
    assert (formal / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.35.0-rc4"
    manifest = json.loads((formal / "lake-manifest.json").read_text())
    mathlib = [p for p in manifest["packages"] if p["name"] == "mathlib"]
    assert len(mathlib) == 1 and mathlib[0]["rev"] == "021c46bdd042f67b538b9f9871d556a93713a9a9"
    source = (formal / "FirstHitDominance.lean").read_text()
    for forbidden in (r"\bsorry\b", r"\badmit\b", r"\bsorryAx\b", r"\bnative_decide\b", r"\baxiom\s+"):
        assert re.search(forbidden, source) is None
    build = (formal / "build-output.txt").read_text()
    assert "Build completed successfully (9040 jobs)." in build
    for name in ("relation_reduces", "relation_support_subset_public",
                 "no_early_rational_relation", "first_hit_dominance"):
        assert f"{name}' depends on axioms: [propext, Classical.choice, Quot.sound]" in build
    for line in (HERE / "SEAL.sha256").read_text().splitlines():
        digest, rel = line.split("  ", 1)
        assert sha(HERE / rel) == digest, rel
    print(json.dumps({"schema":"xedni-first-hit-dominance-verify-v1","status":"PASS",
                      "checked_theorems":4},sort_keys=True))

if __name__ == "__main__":
    main()
