"""Freeze independent Sage planted-point replay."""

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
    planted = json.loads((HERE / "planted_result.json").read_text())
    assert planted["status"] == "PASS_FULL_ASSIGNMENT"
    inputs = {
        "planted_result": HERE / "planted_result.json",
        "planted_protocol": HERE / "planted_protocol.json",
        "geometry": EXP / "n131_phi_torsion_frobenius_domains_20261005" / "m12_d13_static" / "d13_exact_geometry_v1.json",
        "valid_codes": EXP / "n131_d13_phi_branch_equation_20261115" / "valid_codes.json",
        "native_field": CODEGEN / "field.py",
        "native_curve": CODEGEN / "curves.py",
    }
    p = {"kind": "n131_d13_union_m10_sage_protocol_v1",
         "status": "FROZEN_BEFORE_INDEPENDENT_REPLAY",
         "frozen_utc": datetime.now(timezone.utc).isoformat(),
         "curve_id": "EC1N131Ckb1heb5f1998f20b",
         "source_sha256": sha(HERE / "audit_sage.py"),
         "sage_runtime_info_sha256": sha(HERE / "sage_runtime_info.json"),
         "inputs": {k: str(v) for k, v in inputs.items()},
         "input_sha256": {k: sha(v) for k, v in inputs.items()},
         "wall_cap_seconds": 180,
         "rss_cap_bytes": 4*1024**3,
         "claim_boundary": "Independent Sage point/group replay of one planted correctness witness."}
    path = HERE / "sage_protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(p, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
