"""Freeze-measured m11/m12 adjacent-union formula sizes and class counts."""

import hashlib
import json
import sys
import time
from decimal import Decimal, getcontext
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXP = ROOT / "experiments" / "ecc2k130-ic-goal-20260929"
CODEGEN = ROOT / "ecc2k130" / "codegen"
M16 = EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m16_static"
UNION = EXP / "n131_d13_union_m10_formula_20261115"
sys.path[:0] = [str(CODEGEN), str(M16), str(UNION)]

import field
import build_formula as union
import phi_frobenius_sat_gate_m16_sparse_seed_v1 as old

PROTOCOL = HERE / "protocol.json"
RESULT = HERE / "result.json"
R = 680564733841876926932320129493409985129


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def convolve(left, right):
    return [sum(left[j]*right[(i-j)%4] for j in range(4))
            for i in range(4)]


def main():
    p = json.loads(PROTOCOL.read_text())
    assert p["status"] == "FROZEN_BEFORE_SCREEN"
    assert p["source_sha256"] == sha(__file__)
    for name, digest in p["input_sha256"].items():
        assert sha(p["inputs"][name]) == digest
    assert not RESULT.exists()
    geometry = json.loads(Path(p["inputs"]["geometry"]).read_text())
    census = json.loads(Path(p["inputs"]["raw_census"]).read_text())
    valid = json.loads(Path(p["inputs"]["valid_codes"]).read_text())
    prior = json.loads(Path(p["inputs"]["prior_formula_receipt"]).read_text())
    assert len(valid) == 4134 and prior["status"] == "PASS_FORMULA_BUILD"
    classes = [census["original_cofactor_classes_per_position"][str(i)]
               + census["image_cofactor_classes_per_position"][str(i)]
               for i in range(4)]
    assert sum(classes) == 16536
    getcontext().prec = 55
    onb = field.Onb(131)
    basis = [int(x, 16) for x in geometry["domain"]["basis_coordinate_masks_hex"]]
    target = [int(x["phi_coordinate"]) for x in
              geometry["official_single_target_cofactor_fiber"]["four_verified_lifts"]]
    rows = {}
    for m in p["summand_counts"]:
        started = time.monotonic()
        union.M = old.M = m
        formula, primary, roots, prog, node_lits, linear = union.build_formula(
            onb, basis, [code for code, _ in valid], target)
        output = HERE / f"official_q_union_m{m}.xcnf"
        assert not output.exists()
        formula.writeDimacs(output)
        count = [1, 0, 0, 0]
        for _ in range(m):
            count = convolve(count, classes)
        assert sum(count) == 16536**m
        stats = formula.stats()
        rows[str(m)] = {
            "formula_sha256": sha(output),
            "formula_bytes": output.stat().st_size,
            "formula_counts": {**stats, "roots": len(roots),
                               "linear_rows": len(linear)*131},
            "ordered_raw_tuples_by_cofactor_class": [str(x) for x in count],
            "conditional_uniform_subgroup_mean_per_endpoint":
                [str(Decimal(x)/Decimal(R)) for x in count],
            "formula_build_seconds": time.monotonic()-started,
        }
        del formula, primary, roots, prog, node_lits, linear
    result = {
        "kind": "n131_d13_adjacent_union_m11_m12_formula_screen_v1",
        "status": "PASS_EXACT_FORMULA_AND_CLASS_COUNTS",
        "protocol_sha256": sha(PROTOCOL),
        "curve_id": p["curve_id"],
        "candidate_id": None,
        "folded_columns": 4134,
        "raw_choices_per_position": 16536,
        "subgroup_order": str(R),
        "rows": rows,
        "interpretation": "Cofactor-class tuple counts are exact for distinct-position independent source choices; division by subgroup order assumes uniform occupancy within a coset and is not measured yield.",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
