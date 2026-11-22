"""Freeze compatible small-field element decoding and preserve v1 failure."""
import hashlib
import json
from pathlib import Path


D = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


old = json.loads((D / "small_field_protocol.json").read_text())
failure = json.loads((D / "small_field_v1_failure.json").read_text())
assert failure["status"] == "PRODUCER_FAILURE_FIELD_API"
record = dict(old)
record.update({"schema": 2,
               "runner_sha256": sha(D / "small_field_s3_v2_sage.py"),
               "producer_v2_sha256": sha(Path(__file__)),
               "supersedes_protocol_sha256": sha(D / "small_field_protocol.json"),
               "failed_v1_receipt_sha256": sha(D / "small_field_v1_failure.json")})
(D / "small_field_protocol_v2.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
print(sha(D / "small_field_protocol_v2.json"))
