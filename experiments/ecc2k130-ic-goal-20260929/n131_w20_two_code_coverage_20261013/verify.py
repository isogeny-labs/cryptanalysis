"""Read-only exact arithmetic and receipt audit for the fixed-code gate."""
import hashlib
import json
from pathlib import Path
import count

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    for name, digest in protocol["artifact_sha256"].items():
        assert sha(HERE / name) == digest, name
    assert json.loads((HERE / "count_result.json").read_text()) == count.result()
    n131 = count.result()["N131"]["rows"]
    assert n131[1]["proposals_needed_before_half_coverage_permitted"] == "517380078"
    assert n131[1]["minimum_proposal_rate_for_600_seconds"] == "862301"
    lean = (HERE / "lean_check.log").read_text()
    assert "CodeCoverage.successful_targets_le' depends on axioms: [propext, Classical.choice, Quot.sound]" in lean
    assert "CodeCoverage.proposals_517380077_below_half' does not depend on any axioms" in lean
    assert "CodeCoverage.proposals_517380078_reach_half_ceiling' does not depend on any axioms" in lean
    print("PASS_W20_FIXED_CODE_COVERAGE_AUDIT")


if __name__ == "__main__":
    main()
