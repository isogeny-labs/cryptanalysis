"""Check one complete m12 adjacent-union XCNF witness and group sum."""

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
UNION = EXP / "n131_d13_union_m10_formula_20261115"
sys.path[:0] = [str(CODEGEN), str(M16), str(UNION)]

import curves
import field
import build_formula as union
import planted_control as helper
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
    geometry = json.loads(Path(p["inputs"]["geometry"]).read_text())
    valid = json.loads(Path(p["inputs"]["valid_codes"]).read_text())
    onb = field.Onb(131)
    curve = curves.Curve(onb)
    basis = [int(x, 16) for x in geometry["domain"]["basis_coordinate_masks_hex"]]
    official = geometry["official_single_target_cofactor_fiber"]["four_verified_lifts"]
    official_points = [tuple(onb.fromCoords(int(value)) for value in
                             item["target_coordinates"]) for item in official]
    cofactor_points = [curve.add(point, curve.neg(official_points[0]))
                       for point in official_points]
    union.M = old.M = 12
    started = time.monotonic()
    (trial, codes, branches, signs, points, phis, partials,
     target_masks, target_fiber) = helper.choose_case(
         onb, curve, basis, valid, cofactor_points)
    assert len(codes) == len(branches) == len(signs) == len(phis) == 12
    assert len(partials) == 10
    formula, primary, roots, prog, node_lits, linear = union.build_formula(
        onb, basis, [code for code, _ in valid], target_masks)
    before = formula.stats()
    pins = {"endpoint": [0, 0]}
    for position, (code, branch, phi_mask) in enumerate(zip(codes, branches, phis)):
        pins["leaf%d" % position] = [(code >> bit) & 1 for bit in range(13)]
        pins["branch%d" % position] = [branch]
        pins["leafphi%d" % position] = [(phi_mask >> bit) & 1 for bit in range(131)]
    for index, mask in enumerate(partials):
        pins["partial%d" % index] = [(mask >> bit) & 1 for bit in range(131)]
    assignment = old.evaluate_and_check(
        formula, primary, pins, prog, node_lits, linear)
    assert len(assignment) == formula.nVars+1
    running = None
    for point, sign in zip(points, signs):
        running = curve.add(running, curve.neg(point) if sign else point)
    assert running == target_fiber[0]
    result = {
        "kind": "n131_d13_union_m12_planted_xcnf_control_v1",
        "status": "PASS_FULL_ASSIGNMENT",
        "protocol_sha256": sha(PROTOCOL),
        "trial": trial, "seed": helper.SEED,
        "leaf_codes": codes, "leaf_branch_bits": branches,
        "leaf_sign_bits": signs, "leaf_phi_masks": phis,
        "partial_phi_masks": partials,
        "synthetic_target_coordinates": [onb.toCoords(running[0]),
                                         onb.toCoords(running[1])],
        "target_phi_masks": target_masks,
        "formula_counts_before_pins": before,
        "checked_clauses_after_pins": len(formula.clauses),
        "checked_native_xors": len(formula.xors),
        "elapsed_seconds": time.monotonic()-started,
        "claim_boundary": "Complete planted formula and native group replay; independent Sage replay is a separate gate."
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"status": result["status"], "trial": trial,
                      "clauses": len(formula.clauses),
                      "xors": len(formula.xors)}, sort_keys=True))


if __name__ == "__main__":
    main()
