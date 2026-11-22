"""Freeze the N131 adjacent-union m11/m12 cost and class screen."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXP = ROOT / "experiments" / "ecc2k130-ic-goal-20260929"
UNION = EXP / "n131_d13_union_m10_formula_20261115"
RAW = EXP / "n131_d13_phi_raw_fiber_20261115"
CODEGEN = ROOT / "ecc2k130" / "codegen"
M16 = EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m16_static"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    inputs = {
        "geometry": EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m12_d13_static" / "d13_exact_geometry_v1.json",
        "raw_census": RAW / "census_result.json",
        "raw_census_audit": RAW / "audit_result.json",
        "valid_codes": EXP / "n131_d13_phi_branch_equation_20261115" / "valid_codes.json",
        "valid_codes_result": EXP / "n131_d13_phi_branch_equation_20261115" / "valid_codes_result.json",
        "prior_formula_receipt": UNION / "formula_receipt.json",
        "prior_formula_source": UNION / "build_formula.py",
        "old_template": M16 / "phi_frobenius_sat_gate_m16_sparse_seed_v1.py",
        "field_source": CODEGEN / "field.py",
        "cnf_source": CODEGEN / "cnf.py",
        "ir_source": CODEGEN / "ir.py",
    }
    assert json.loads(inputs["raw_census_audit"].read_text())["status"] == "PASS_ALL_VALID_SELECTORS"
    assert json.loads(inputs["valid_codes_result"].read_text())["status"] == "PASS_EXACT_ENUMERATION"
    p = {"kind": "n131_d13_union_arity_screen_protocol_v1",
         "status": "FROZEN_BEFORE_SCREEN",
         "frozen_utc": datetime.now(timezone.utc).isoformat(),
         "curve_id": "EC1N131Ckb1heb5f1998f20b",
         "workload_id": "3c1992b7c92f",
         "target_count": 1,
         "summand_counts": [11, 12],
         "source_sha256": sha(HERE / "screen.py"),
         "inputs": {k: str(v) for k, v in inputs.items()},
         "input_sha256": {k: sha(v) for k, v in inputs.items()},
         "claim_boundary": "Exact formula counts and torsion-class tuple counts; uniform subgroup occupancy is a labeled model, not natural yield."}
    path = HERE / "protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(p, indent=2, sort_keys=True)+"\n")
    print(path)


if __name__ == "__main__":
    main()
