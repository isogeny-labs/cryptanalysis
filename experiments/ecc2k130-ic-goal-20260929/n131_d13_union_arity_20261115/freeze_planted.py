"""Freeze the m12 planted control after the arity cost screen."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXP = ROOT / "experiments" / "ecc2k130-ic-goal-20260929"
UNION = EXP / "n131_d13_union_m10_formula_20261115"
CODEGEN = ROOT / "ecc2k130" / "codegen"
M16 = EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m16_static"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    screen = json.loads((HERE / "result.json").read_text())
    assert screen["status"] == "PASS_EXACT_FORMULA_AND_CLASS_COUNTS"
    inputs = {
        "screen_protocol": HERE / "protocol.json",
        "screen_result": HERE / "result.json",
        "m12_formula": HERE / "official_q_union_m12.xcnf",
        "geometry": EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m12_d13_static" / "d13_exact_geometry_v1.json",
        "valid_codes": EXP / "n131_d13_phi_branch_equation_20261115" / "valid_codes.json",
        "formula_source": UNION / "build_formula.py",
        "prior_planted_helper": UNION / "planted_control.py",
        "curve_source": CODEGEN / "curves.py",
        "field_source": CODEGEN / "field.py",
        "old_template": M16 / "phi_frobenius_sat_gate_m16_sparse_seed_v1.py",
    }
    assert screen["rows"]["12"]["formula_sha256"] == sha(inputs["m12_formula"])
    p = {
        "kind": "n131_d13_union_m12_planted_protocol_v1",
        "status": "FROZEN_BEFORE_PLANTED_CONTROL",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "curve_id": "EC1N131Ckb1heb5f1998f20b",
        "summand_count": 12, "seed": 2026111510,
        "source_sha256": sha(HERE / "planted_m12.py"),
        "inputs": {k: str(v) for k, v in inputs.items()},
        "input_sha256": {k: sha(v) for k, v in inputs.items()},
        "wall_cap_seconds": 60,
        "claim_boundary": "Complete planted m12 control; ordinary-target result requires unpinned query and independent replay."
    }
    path = HERE / "planted_protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(p, indent=2, sort_keys=True)+"\n")
    print(path)


if __name__ == "__main__":
    main()
