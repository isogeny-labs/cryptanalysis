"""Freeze independent installed-Sage branch replay."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    original = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "audit_result.json").read_text())
    assert result["status"] == "PASS_ALL_VALID_SELECTORS_BOTH_BRANCHES"
    inputs = {"geometry": Path(original["inputs"]["geometry"]),
              "audit_result": HERE / "audit_result.json"}
    record = {
        "kind": "n131_d13_union_phi_branch_sage_protocol_v1",
        "status": "FROZEN_BEFORE_INDEPENDENT_AUDIT",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "curve_id": original["curve_id"],
        "inputs": {k: str(v) for k, v in inputs.items()},
        "input_sha256": {k: sha(v) for k, v in inputs.items()},
        "source_sha256": sha(HERE / "audit_sage.py"),
        "sage_runtime_info_sha256": sha(HERE / "sage_runtime_info.json"),
        "wall_cap_seconds": 180,
        "rss_cap_bytes": 4*1024**3,
        "claim_boundary": "Independent finite-field and curve replay of both phi-chart formulas, without a SAT solver cost measurement.",
    }
    path = HERE / "audit_sage_protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
