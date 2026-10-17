"""Freeze two exhaustive small-field S3 bridge checks."""
import hashlib
import json
from pathlib import Path


D = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


record = {"schema": 1,
          "runner_sha256": sha(D / "small_field_s3_sage.py"),
          "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
          "field_degrees": [5, 7],
          "input_law": "every nonzero reciprocal-x triple with rational parent and S3=0"}
(D / "small_field_protocol.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
print(sha(D / "small_field_protocol.json"))
