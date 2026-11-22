"""Freeze the exact official-Q ten-leaf formula cost screen."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CODEGEN = ROOT / "ecc2k130" / "codegen"
EXP = ROOT / "experiments" / "ecc2k130-ic-goal-20260929"
M16 = EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m16_static"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    inputs = {
        "geometry": EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m12_d13_static" / "d13_exact_geometry_v1.json",
        "valid_codes": EXP / "n131_d13_phi_branch_equation_20261115" / "valid_codes.json",
        "valid_codes_result": EXP / "n131_d13_phi_branch_equation_20261115" / "valid_codes_result.json",
        "chart_replay_result": EXP / "n131_d13_phi_branch_equation_20261115" / "audit_sage_v3_result.json",
        "old_template": M16 / "phi_frobenius_sat_gate_m16_sparse_seed_v1.py",
        "ir": CODEGEN / "ir.py",
        "cnf": CODEGEN / "cnf.py",
        "decomp": CODEGEN / "decomp.py",
        "build": CODEGEN / "build.py",
        "field": CODEGEN / "field.py",
    }
    valid = json.loads(inputs["valid_codes_result"].read_text())
    replay = json.loads(inputs["chart_replay_result"].read_text())
    assert valid["status"] == "PASS_EXACT_ENUMERATION"
    assert replay["status"] == "PASS_ALL_VALID_SELECTORS"
    assert valid["count"] == replay["valid_selectors"] == 4134
    assert valid["codes_sha256"] == sha(inputs["valid_codes"])
    p = {"kind": "n131_d13_union_m10_formula_protocol_v1",
         "status": "FROZEN_BEFORE_BUILD",
         "frozen_utc": datetime.now(timezone.utc).isoformat(),
         "curve_id": "EC1N131Ckb1heb5f1998f20b",
         "subspace_dimension": 13,
         "summand_count": 10,
         "target_count": 1,
         "endpoint": "four verified cofactor lifts of frozen official Q",
         "source_sha256": sha(HERE / "build_formula.py"),
         "inputs": {k: str(v) for k, v in inputs.items()},
         "input_sha256": {k: sha(v) for k, v in inputs.items()},
         "memory_cap_bytes": 4*1024**3,
         "wall_cap_seconds": 600,
         "claim_boundary": "Formula construction and planted correctness control; an ordinary solver query requires a separate frozen run."}
    path = HERE / "protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(p, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
