"""Freeze the corrected halftrace assertion while retaining both failures."""
import hashlib
import json
from pathlib import Path


D = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


old = json.loads((D / "n131_leaf_projection_protocol_v2.json").read_text())
failure = json.loads((D / "n131_v2_failure.json").read_text())
assert failure["status"] == "PRODUCER_FAILURE_HALFTRACE_ASSERTION"
assert sha(D / "n131_leaf_projection_protocol_v2.json") == failure["protocol_sha256"]
record = dict(old)
record.update({"schema": 3,
               "runner_sha256": sha(D / "n131_leaf_projection_v3_sage.py"),
               "producer_v3_sha256": sha(Path(__file__)),
               "supersedes_protocol_sha256": sha(D / "n131_leaf_projection_protocol_v2.json"),
               "failed_v2_receipt_sha256": sha(D / "n131_v2_failure.json")})
(D / "n131_leaf_projection_protocol_v3.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
print(sha(D / "n131_leaf_projection_protocol_v3.json"))
