"""Freeze existing factor logs and the public row before scalar recovery."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PIPE = GOAL / "n41_w6_s8_pipeline"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    inputs = {
        "union_rows": HERE / "union_rows.json",
        "ordinary_receipt": HERE / "ordinary_receipt.json",
        "replay_result": HERE / "replay_result.json",
        "logs": PIPE / "factor_logs.json",
        "log_replay": PIPE / "factor_logs_sage_replay.json",
        "base_map": PIPE / "base_orbit_coefficients.json",
        "public": GOAL / "n41_adjacent_pairpair" / "public_target.json",
        "fixture": GOAL / "n41_adjacent_pairpair" / "validation_scalar.json",
    }
    assert json.loads(inputs["replay_result"].read_text())["status"] == "PASS_CONTROL_AND_ORDINARY"
    assert json.loads(inputs["log_replay"].read_text())["status"] == "PASS"
    record = {
        "kind": "n41_w6_adjacent_union_factor_log_recovery_protocol_v1",
        "status": "FROZEN_BEFORE_RECOVERY",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_id": None,
        "inputs": {name: str(path) for name, path in inputs.items()},
        "input_sha256": {name: sha(path) for name, path in inputs.items()},
        "source_sha256": sha(HERE / "recover.py"),
        "sage_runtime_info_sha256": sha(HERE / "sage_runtime_info.json"),
        "claim_boundary": "Existing verified factor logs are reusable setup; time only target-dependent row mapping, scalar recovery, and group replay here. Ordinary-host component timing is diagnostic.",
    }
    path = HERE / "recovery_protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
