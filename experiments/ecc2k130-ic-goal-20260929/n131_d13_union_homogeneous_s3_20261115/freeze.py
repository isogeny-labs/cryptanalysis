"""Freeze homogeneous S3 source and exact official-point inputs."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXP = ROOT / "experiments" / "ecc2k130-ic-goal-20260929"
CODEGEN = ROOT / "ecc2k130" / "codegen"
M16 = EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m16_static"
UNION = EXP / "n131_d13_union_m10_formula_20261115"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert "sorryAx" not in (HERE / "lean.stdout").read_text()
    assert not (HERE / "lean.stderr").read_text()
    prior = json.loads((UNION / "formula_receipt.json").read_text())
    assert prior["status"] == "PASS_FORMULA_BUILD"
    inputs = {
        "geometry": EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m12_d13_static" / "d13_exact_geometry_v1.json",
        "valid_codes": EXP / "n131_d13_phi_branch_equation_20261115" / "valid_codes.json",
        "valid_codes_result": EXP / "n131_d13_phi_branch_equation_20261115" / "valid_codes_result.json",
        "branch_source": EXP / "n131_d13_phi_branch_equation_20261115" / "BranchEquation.lean",
        "prior_formula_receipt": UNION / "formula_receipt.json",
        "prior_formula_source": UNION / "build_formula.py",
        "old_template": M16 / "phi_frobenius_sat_gate_m16_sparse_seed_v1.py",
        "ir": CODEGEN / "ir.py", "cnf": CODEGEN / "cnf.py",
        "decomp": CODEGEN / "decomp.py", "build": CODEGEN / "build.py",
        "field": CODEGEN / "field.py",
    }
    p = {
        "kind": "n131_d13_union_homogeneous_s3_formula_protocol_v1",
        "status": "FROZEN_BEFORE_BUILD",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "curve_id": "EC1N131Ckb1heb5f1998f20b",
        "summand_count": 10, "subspace_dimension": 13,
        "target_count": 1,
        "source_sha256": sha(HERE / "build_rational.py"),
        "lean_source_sha256": sha(HERE / "HomogeneousS3.lean"),
        "lean_stdout_sha256": sha(HERE / "lean.stdout"),
        "inputs": {k: str(v) for k, v in inputs.items()},
        "input_sha256": {k: sha(v) for k, v in inputs.items()},
        "wall_cap_seconds": 60,
        "claim_boundary": "Complete official-point formula-size screen. A planted assignment and independent replay are separate gates."
    }
    path = HERE / "protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(p, indent=2, sort_keys=True)+"\n")
    print(path)


if __name__ == "__main__":
    main()
