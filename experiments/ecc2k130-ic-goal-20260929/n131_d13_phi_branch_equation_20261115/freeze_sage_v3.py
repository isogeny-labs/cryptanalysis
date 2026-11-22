"""Freeze the field-chart replay after both capped point-reconstruction runs."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "n131_d13_phi_raw_fiber_20261115" / "audit_result.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    v2 = json.loads((HERE / "audit_sage_protocol_v2.json").read_text())
    prior = json.loads((HERE / "audit_sage_status.json").read_text())
    assert prior["status"] == "CAPPED_180_SECONDS"
    assert v2["status"] == "FROZEN_VALID_CODES_REPLAY"
    assert not (HERE / "audit_sage_v2_result.json").read_text()
    assert "AssertionError" in (HERE / "audit_sage_v2.stderr").read_text()
    status_path = HERE / "audit_sage_v2_status.json"
    status = json.loads(status_path.read_text())
    assert status["status"] == "CAPPED_180_SECONDS"
    status.update({"protocol_sha256": sha(HERE / "audit_sage_protocol_v2.json"),
                   "source_sha256": sha(HERE / "audit_sage_v2.py"),
                   "stderr_sha256": sha(HERE / "audit_sage_v2.stderr")})
    status_path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    assert json.loads(RAW.read_text())["status"] == "PASS_ALL_VALID_SELECTORS"
    inputs = {"geometry": Path(v2["inputs"]["geometry"]),
              "audit_result": HERE / "audit_result.json",
              "valid_codes": HERE / "valid_codes.json",
              "raw_sage_result": RAW}
    record = {"kind": "n131_d13_union_phi_branch_sage_protocol_v3",
              "status": "FROZEN_FIELD_CHART_REPLAY",
              "frozen_utc": datetime.now(timezone.utc).isoformat(),
              "curve_id": v2["curve_id"],
              "amends_protocol_sha256": sha(HERE / "audit_sage_protocol_v2.json"),
              "capped_attempt_status_sha256": sha(status_path),
              "claim_boundary": "Independent polynomial-field phi-chart conversion on each frozen valid selector. The group map is established by the prior all-selector Sage raw-fiber replay.",
              "inputs": {k: str(v) for k, v in inputs.items()},
              "input_sha256": {k: sha(v) for k, v in inputs.items()},
              "source_sha256": sha(HERE / "audit_sage_v3.py"),
              "sage_runtime_info_sha256": sha(HERE / "sage_runtime_info.json"),
              "wall_cap_seconds": 180,
              "rss_cap_bytes": 4*1024**3}
    path = HERE / "audit_sage_protocol_v3.json"
    assert not path.exists()
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
