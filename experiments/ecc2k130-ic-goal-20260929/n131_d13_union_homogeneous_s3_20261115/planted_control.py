"""Replay the prior ten-leaf planted witness through homogeneous S3."""

import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXP = ROOT / "experiments" / "ecc2k130-ic-goal-20260929"
CODEGEN = ROOT / "ecc2k130" / "codegen"
M16 = EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m16_static"
sys.path[:0] = [str(HERE), str(CODEGEN), str(M16)]

import field
import build_rational as rational
import phi_frobenius_sat_gate_m16_sparse_seed_v1 as old

PROTOCOL = HERE / "planted_protocol.json"
RESULT = HERE / "planted_result.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = json.loads(PROTOCOL.read_text())
    assert p["status"] == "FROZEN_BEFORE_PLANTED_CONTROL"
    assert p["source_sha256"] == sha(__file__)
    for name, digest in p["input_sha256"].items():
        assert sha(p["inputs"][name]) == digest
    assert not RESULT.exists()
    prior = json.loads(Path(p["inputs"]["prior_planted"]).read_text())
    assert prior["status"] == "PASS_FULL_ASSIGNMENT"
    geometry = json.loads(rational.GEOMETRY.read_text())
    valid = json.loads(rational.VALID.read_text())
    basis = [int(x, 16) for x in geometry["domain"]["basis_coordinate_masks_hex"]]
    old.DIM, old.M = rational.DIM, rational.M
    started = time.monotonic()
    formula, primary, roots, prog, node_lits, linear = rational.build_formula(
        field.Onb(rational.N), basis, [code for code, _ in valid],
        prior["target_phi_masks"])
    stats = formula.stats()
    pins = {"one": [1], "endpoint": [0, 0]}
    for position, (code, branch) in enumerate(
            zip(prior["leaf_codes"], prior["leaf_branch_bits"])):
        pins["leaf%d" % position] = [(code >> bit) & 1
                                     for bit in range(rational.DIM)]
        pins["branch%d" % position] = [branch]
    for index, mask in enumerate(prior["partial_phi_masks"]):
        pins["partial%d" % index] = [(mask >> bit) & 1
                                     for bit in range(rational.N)]
    assignment = old.evaluate_and_check(
        formula, primary, pins, prog, node_lits, linear)
    assert len(assignment) == formula.nVars+1
    result = {
        "kind": "n131_d13_union_m10_homogeneous_planted_control_v1",
        "status": "PASS_FULL_ASSIGNMENT",
        "protocol_sha256": sha(PROTOCOL),
        "formula_counts_before_pins": stats,
        "checked_clauses_after_pins": len(formula.clauses),
        "checked_native_xors": len(formula.xors),
        "branch_bits": prior["leaf_branch_bits"],
        "elapsed_seconds": time.monotonic()-started,
        "claim_boundary": "Exact planted XCNF assignment; prior independent Sage group replay supplies the point-sum control."
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
