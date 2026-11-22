"""Deterministically compress both checked XCNFs with byte replay receipts."""

import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


frozen = json.loads((HERE / "archive_protocol.json").read_text())
assert frozen["status"] == "FROZEN_BEFORE_DIRECT_ADDITION_XCNF_ARCHIVE"
for key, filename in {
    "source": "archive.py",
    "control": "control_result.json",
    "query": "query_result.json",
    "terminal_audit": "query_audit_result.json",
}.items():
    assert frozen["sha256"][key] == sha(HERE / filename), key

receipts = {}
for label, filename, result_name in (
    ("control", "control.xcnf", "control_result.json"),
    ("public", "ordinary.xcnf", "query_result.json"),
):
    result = json.loads((HERE / result_name).read_text())
    raw = HERE / filename
    packed = HERE / (filename + ".gz")
    profile = result["formula"]
    assert sha(raw) == profile["xcnf_sha256"]
    assert raw.stat().st_size == profile["xcnf_bytes"]
    with raw.open("rb") as source, packed.open("xb") as destination:
        with gzip.GzipFile(filename="", mode="wb", fileobj=destination,
                           compresslevel=3, mtime=0) as stream:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                stream.write(chunk)
    digest, size = hashlib.sha256(), 0
    with gzip.open(packed, "rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    assert digest.hexdigest() == profile["xcnf_sha256"]
    assert size == profile["xcnf_bytes"]
    receipts[label] = {
        "raw_sha256": digest.hexdigest(),
        "raw_bytes": size,
        "gzip_sha256": sha(packed),
        "gzip_bytes": packed.stat().st_size,
    }
with (HERE / "archive_result.json").open("x") as stream:
    json.dump({"status": "PASS_DIRECT_ADDITION_BOTH_XCNF_ARCHIVE_REPLAY",
               "files": receipts,
               "archive_protocol_sha256": sha(HERE / "archive_protocol.json")},
              stream, sort_keys=True, indent=2)
    stream.write("\n")
print("PASS_DIRECT_ADDITION_BOTH_XCNF_ARCHIVE_REPLAY", flush=True)
