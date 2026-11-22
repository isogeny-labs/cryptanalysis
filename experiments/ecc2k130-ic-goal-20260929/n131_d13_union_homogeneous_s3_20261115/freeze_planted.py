"""Freeze planted correctness replay after the formula-size screen."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
PRIOR = EXP / "n131_d13_union_m10_formula_20261115"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    receipt = json.loads((HERE / "formula_receipt.json").read_text())
    prior = json.loads((PRIOR / "planted_result.json").read_text())
    assert receipt["status"] == "PASS_FORMULA_BUILD"
    assert prior["status"] == "PASS_FULL_ASSIGNMENT"
    inputs = {
        "formula_receipt": HERE / "formula_receipt.json",
        "formula_protocol": HERE / "protocol.json",
        "formula_source": HERE / "build_rational.py",
        "prior_planted": PRIOR / "planted_result.json",
        "prior_sage_replay": PRIOR / "sage_result.json",
    }
    p = {
        "kind": "n131_d13_union_homogeneous_planted_protocol_v1",
        "status": "FROZEN_BEFORE_PLANTED_CONTROL",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "curve_id": "EC1N131Ckb1heb5f1998f20b",
        "source_sha256": sha(HERE / "planted_control.py"),
        "inputs": {k: str(v) for k, v in inputs.items()},
        "input_sha256": {k: sha(v) for k, v in inputs.items()},
        "wall_cap_seconds": 60,
        "claim_boundary": "One complete known-witness formula check; no natural-yield inference."
    }
    path = HERE / "planted_protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(p, indent=2, sort_keys=True)+"\n")
    print(path)


if __name__ == "__main__":
    main()
