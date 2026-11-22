"""Read-only replay of the archived constructed SAT formula."""

import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAT = HERE / "sat"
receipt = json.loads((HERE / "archive_receipt.json").read_text())
control = json.loads((SAT / "control_result.json").read_text())
packed = SAT / "control.xcnf.gz"
assert receipt["status"] == "PASS_SIGNATURE_CONTROL_XCNF_GZIP_BYTE_REPLAY"
assert hashlib.sha256(packed.read_bytes()).hexdigest() == receipt["gzip_sha256"]
digest = hashlib.sha256()
size = 0
with gzip.open(packed, "rb") as stream:
    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            break
        digest.update(chunk)
        size += len(chunk)
assert digest.hexdigest() == receipt["raw_sha256"] == control["formula"]["xcnf_sha256"]
assert size == receipt["raw_bytes"] == control["formula"]["xcnf_bytes"]
print("PASS_SIGNATURE_CONTROL_ARCHIVE_REPLAY", size)
