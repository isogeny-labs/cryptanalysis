"""Freeze source and inputs for the d13 valid-selector list."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    first = json.loads((HERE / "protocol.json").read_text())
    inputs = {"geometry": Path(first["inputs"]["geometry"]),
              "audit_result": HERE / "audit_result.json",
              "field_source": Path(first["inputs"]["field_source"]),
              "curve_source": Path(first["inputs"]["curve_source"]),
              "audit_curve_source": Path(first["inputs"]["audit_curve_source"])}
    record = {"kind": "n131_d13_valid_selector_freeze_v1",
              "status": "FROZEN_BEFORE_ENUMERATION",
              "frozen_utc": datetime.now(timezone.utc).isoformat(),
              "curve_id": first["curve_id"],
              "inputs": {k: str(v) for k, v in inputs.items()},
              "input_sha256": {k: sha(v) for k, v in inputs.items()},
              "source_sha256": sha(HERE / "enumerate_valid.py"),
              "wall_cap_seconds": 180,
              "rss_cap_bytes": 4*1024**3,
              "claim_boundary": "Exact source-selector enumeration for replay; no relation-yield claim."}
    path = HERE / "valid_codes_protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
