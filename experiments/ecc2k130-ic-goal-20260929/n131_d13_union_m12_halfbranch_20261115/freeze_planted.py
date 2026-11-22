"""Freeze the complete assignment control for the half-fixed formula."""

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
    formula = json.loads((HERE / "formula_receipt.json").read_text())
    classes = json.loads((HERE / "class_result.json").read_text())
    assert formula["status"] == "PASS_FORMULA_BUILD"
    assert classes["status"] == "PASS_EXACT_CLASS_COUNTS"
    inputs = {
        "build_protocol": HERE / "protocol.json",
        "formula_receipt": HERE / "formula_receipt.json",
        "class_result": HERE / "class_result.json",
        "formula": HERE / "official_q_d13_halfbranch_m12_v1.xcnf",
        "geometry": EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m12_d13_static" / "d13_exact_geometry_v1.json",
        "valid_codes": EXP / "n131_d13_phi_branch_equation_20261115" / "valid_codes.json",
        "formula_source": HERE / "build_formula.py",
        "curve_source": CODEGEN / "curves.py",
        "field_source": CODEGEN / "field.py",
        "old_template": M16 / "phi_frobenius_sat_gate_m16_sparse_seed_v1.py",
    }
    assert formula["formula_sha256"] == sha(inputs["formula"])
    p = {
        "kind": "n131_d13_halfbranch_m12_planted_protocol_v1",
        "status": "FROZEN_BEFORE_PLANTED_CONTROL",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "curve_id": "EC1N131Ckb1heb5f1998f20b",
        "summand_count": 12,
        "seed": 2026111512,
        "fixed_original_positions": [0, 2, 4, 6, 8, 10],
        "source_sha256": sha(HERE / "planted_m12.py"),
        "inputs": {key: str(value) for key, value in inputs.items()},
        "input_sha256": {key: sha(value) for key, value in inputs.items()},
        "wall_cap_seconds": 60,
        "claim_boundary": "Complete planted assignment; independent Sage replay and an unpinned ordinary query are separate gates.",
    }
    path = HERE / "planted_protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(p, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
