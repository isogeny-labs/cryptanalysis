"""Amend the capped Sage scan to replay the frozen valid-code list."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    v1 = json.loads((HERE / "audit_sage_protocol.json").read_text())
    status = json.loads((HERE / "audit_sage_status.json").read_text())
    enumerated = json.loads((HERE / "valid_codes_result.json").read_text())
    assert status["status"] == "CAPPED_180_SECONDS"
    assert enumerated["status"] == "PASS_EXACT_ENUMERATION"
    assert enumerated["codes_sha256"] == sha(HERE / "valid_codes.json")
    inputs = {"geometry": Path(v1["inputs"]["geometry"]),
              "audit_result": HERE / "audit_result.json",
              "valid_codes": HERE / "valid_codes.json",
              "valid_codes_result": HERE / "valid_codes_result.json"}
    record = {"kind": "n131_d13_union_phi_branch_sage_protocol_v2",
              "status": "FROZEN_VALID_CODES_REPLAY",
              "frozen_utc": datetime.now(timezone.utc).isoformat(),
              "curve_id": v1["curve_id"],
              "amends_protocol_sha256": sha(HERE / "audit_sage_protocol.json"),
              "capped_attempt_status_sha256": sha(HERE / "audit_sage_status.json"),
              "inputs": {k: str(v) for k, v in inputs.items()},
              "input_sha256": {k: sha(v) for k, v in inputs.items()},
              "source_sha256": sha(HERE / "audit_sage_v2.py"),
              "sage_runtime_info_sha256": sha(HERE / "sage_runtime_info.json"),
              "wall_cap_seconds": 180,
              "rss_cap_bytes": 4*1024**3,
              "claim_boundary": "Independent field and curve replay of each frozen valid selector; eligibility-list completeness is established by the separate exact enumeration and prior full Sage raw-base audit."}
    path = HERE / "audit_sage_protocol_v2.json"
    assert not path.exists()
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
