"""Freeze the even-position original-source m12 cost and class screen."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXP = ROOT / "experiments" / "ecc2k130-ic-goal-20260929"
CODEGEN = ROOT / "ecc2k130" / "codegen"
M16 = EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m16_static"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    inputs = {
        "geometry": EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m12_d13_static" / "d13_exact_geometry_v1.json",
        "valid_codes": EXP / "n131_d13_phi_branch_equation_20261115" / "valid_codes.json",
        "valid_codes_result": EXP / "n131_d13_phi_branch_equation_20261115" / "valid_codes_result.json",
        "chart_replay_result": EXP / "n131_d13_phi_branch_equation_20261115" / "audit_sage_v3_result.json",
        "raw_census": EXP / "n131_d13_phi_raw_fiber_20261115" / "census_result.json",
        "raw_census_audit": EXP / "n131_d13_phi_raw_fiber_20261115" / "audit_result.json",
        "full_m12_receipt": EXP / "n131_d13_union_arity_20261115" / "result.json",
        "old_template": M16 / "phi_frobenius_sat_gate_m16_sparse_seed_v1.py",
        "ir": CODEGEN / "ir.py", "cnf": CODEGEN / "cnf.py",
        "decomp": CODEGEN / "decomp.py", "build": CODEGEN / "build.py",
        "field": CODEGEN / "field.py",
    }
    assert json.loads(inputs["valid_codes_result"].read_text())["status"] == "PASS_EXACT_ENUMERATION"
    assert json.loads(inputs["chart_replay_result"].read_text())["status"] == "PASS_ALL_VALID_SELECTORS"
    assert json.loads(inputs["raw_census_audit"].read_text())["status"] == "PASS_ALL_VALID_SELECTORS"
    assert json.loads(inputs["full_m12_receipt"].read_text())["status"] == "PASS_EXACT_FORMULA_AND_CLASS_COUNTS"
    p = {
        "kind": "n131_d13_halfbranch_m12_protocol_v1",
        "status": "FROZEN_BEFORE_BUILD",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "curve_id": "EC1N131Ckb1heb5f1998f20b",
        "workload_id": "3c1992b7c92f",
        "subgroup_order": "680564733841876926932320129493409985129",
        "subspace_dimension": 13,
        "summand_count": 12,
        "fixed_original_positions": [0, 2, 4, 6, 8, 10],
        "target_count": 1,
        "endpoint": "four verified cofactor lifts of frozen official Q",
        "source_sha256": sha(HERE / "build_formula.py"),
        "class_source_sha256": sha(HERE / "class_screen.py"),
        "inputs": {key: str(value) for key, value in inputs.items()},
        "input_sha256": {key: sha(value) for key, value in inputs.items()},
        "memory_cap_bytes": 4 * 1024**3,
        "wall_cap_seconds": 600,
        "claim_boundary": "Exact branch-restricted formula and cofactor-class tuple cost; correctness controls precede an ordinary solver query.",
    }
    path = HERE / "protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(p, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
