"""Freeze corrected W23 halftrace input law, retaining the v1 failure."""
import hashlib
import json
from pathlib import Path


D = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


old = json.loads((D / "n131_leaf_projection_protocol.json").read_text())
failure = json.loads((D / "n131_v1_failure.json").read_text())
assert failure["status"] == "PRODUCER_FAILURE_INPUT_MODEL"
assert sha(D / "n131_leaf_projection_protocol.json") == failure["protocol_sha256"]
record = dict(old)
record.update({"schema": 2,
               "runner_sha256": sha(D / "n131_leaf_projection_v2_sage.py"),
               "producer_v2_sha256": sha(Path(__file__)),
               "supersedes_protocol_sha256": sha(D / "n131_leaf_projection_protocol.json"),
               "failed_v1_receipt_sha256": sha(D / "n131_v1_failure.json"),
               "source_parameter_model": "mask encodes w=u^2+u; u=halftrace(w)",
               "input_law": "all eight archived W23 sample edges with four sign combinations each"})
(D / "n131_leaf_projection_protocol_v2.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
print(sha(D / "n131_leaf_projection_protocol_v2.json"))
