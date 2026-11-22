"""Freeze planted union-formula check against the completed official build."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXP = ROOT / "experiments" / "ecc2k130-ic-goal-20260929"
CODEGEN = ROOT / "ecc2k130" / "codegen"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    prior = json.loads((HERE / "formula_receipt.json").read_text())
    assert prior["status"] == "PASS_FORMULA_BUILD"
    assert prior["formula_sha256"] == sha(HERE / "official_q_d13_union_m10_v1.xcnf")
    inputs = {
        "formula_protocol": HERE / "protocol.json",
        "formula_receipt": HERE / "formula_receipt.json",
        "formula_source": HERE / "build_formula.py",
        "geometry": EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m12_d13_static" / "d13_exact_geometry_v1.json",
        "valid_codes": EXP / "n131_d13_phi_branch_equation_20261115" / "valid_codes.json",
        "curve_source": CODEGEN / "curves.py",
    }
    p = {"kind": "n131_d13_union_m10_planted_control_protocol_v1",
         "status": "FROZEN_BEFORE_PLANTED_CONTROL",
         "frozen_utc": datetime.now(timezone.utc).isoformat(),
         "curve_id": "EC1N131Ckb1heb5f1998f20b",
         "seed": 2026111510, "max_trials": 100,
         "source_sha256": sha(HERE / "planted_control.py"),
         "inputs": {k: str(v) for k, v in inputs.items()},
         "input_sha256": {k: sha(v) for k, v in inputs.items()},
         "wall_cap_seconds": 600,
         "memory_cap_bytes": 4*1024**3,
         "claim_boundary": "Planted correctness control on a synthetic point; no natural relation-yield estimate."}
    path = HERE / "planted_protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(p, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
