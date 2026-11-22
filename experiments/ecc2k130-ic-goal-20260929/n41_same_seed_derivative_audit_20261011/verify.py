"""Bind the capped producer, corrected census, and independent Sage replay."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / "n41_same_seed_derivative_collapse_20261011"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    original = json.loads((PRIOR / "protocol.json").read_text())
    failure = json.loads((PRIOR / "failure_v1.json").read_text())
    corrected = json.loads((PRIOR / "protocol_v2.json").read_text())
    producer = json.loads((PRIOR / "result_v2.json").read_text())
    first_audit = json.loads((HERE / "protocol.json").read_text())
    audit_failure = json.loads((HERE / "failure_v1.json").read_text())
    audit_protocol = json.loads((HERE / "protocol_v2.json").read_text())
    sage = json.loads((HERE / "sage_audit_v2.json").read_text())
    assert original["sha256"]["run"] == sha(PRIOR / "run.py")
    assert failure["status"] == "CAP_EXCEEDED_AT_ROTATION_BOUNDARY"
    assert failure["protocol_sha256"] == sha(PRIOR / "protocol.json")
    assert failure["source_sha256"] == sha(PRIOR / "run.py")
    assert not failure["result_exists"] and not (PRIOR / "result.json").exists()
    assert corrected["sha256"]["run"] == sha(PRIOR / "run_v2.py")
    assert corrected["prior_failure_sha256"] == sha(PRIOR / "failure_v1.json")
    assert producer["protocol_sha256"] == sha(PRIOR / "protocol_v2.json")
    assert producer["source_sha256"] == sha(PRIOR / "run_v2.py")
    assert producer["status"] == "COMPLETE"
    assert producer["elapsed_ns"] / 1e9 < corrected["cap_seconds"]
    assert producer["peak_rss_bytes"] < corrected["rss_cap_bytes"]
    assert first_audit["sha256"]["audit"] == sha(HERE / "sage_audit.py")
    assert audit_failure["status"] == "AUDITOR_SERIALIZATION_KEY_MISMATCH"
    assert audit_failure["source_sha256"] == sha(HERE / "sage_audit.py")
    assert audit_failure["protocol_sha256"] == sha(HERE / "protocol.json")
    assert audit_protocol["prior_failure_sha256"] == sha(HERE / "failure_v1.json")
    assert audit_protocol["sha256"]["audit"] == sha(HERE / "sage_audit_v2.py")
    assert audit_protocol["sha256"]["producer"] == sha(PRIOR / "result_v2.json")
    assert audit_protocol["sha256"]["runtime"] == sha(HERE / "sage_runtime_info.json")
    assert json.loads((HERE / "sage_runtime_info.json").read_text())["status"] == "verified"
    assert sage["status"] == "PASS_INDEPENDENT_SAGE_SHARED_SEED_CENSUS"
    assert sage["protocol_sha256"] == sha(HERE / "protocol_v2.json")
    assert sage["producer_sha256"] == sha(PRIOR / "result_v2.json")
    assert sage["elapsed_ns"] / 1e9 < audit_protocol["cap_seconds"]
    assert sage["peak_rss_bytes"] < audit_protocol["rss_cap_bytes"]
    row = producer["rotations"]["0"]
    assert all(sage["checked"][name] == value for name, value in row.items()
               if name in sage["checked"])
    assert row["source_quartets"] == 1620
    assert row["repeated_keys"] == 378
    assert row["sign0_single_output_repeated_keys"] == 0
    assert row["all_sign_identical_output_sets_repeated_keys"] == 0
    assert row["all_sign_total_distinct_by_key"] == row["signed_assignments"] == 25920
    assert row["example_nocollapse"]["seed"] == 1
    assert row["example_nocollapse"]["difference"] == 4
    out = {"status": "PASS_SHARED_SEED_DERIVATIVE_BOUNDARY",
           "quartets": row["source_quartets"], "repeated_keys": row["repeated_keys"],
           "signed_outputs": row["all_sign_total_distinct_by_key"],
           "producer_sha256": sha(PRIOR / "result_v2.json"),
           "sage_sha256": sha(HERE / "sage_audit_v2.json"),
           "prior_failure_sha256": sha(PRIOR / "failure_v1.json"),
           "audit_failure_sha256": sha(HERE / "failure_v1.json")}
    (HERE / "verification.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
