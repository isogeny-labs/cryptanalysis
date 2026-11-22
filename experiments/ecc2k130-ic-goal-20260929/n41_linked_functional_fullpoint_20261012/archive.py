"""Byte-preserving gzip archive of the three linked N41 attempts."""

import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FORMULAS = (
    "control.xcnf", "public.xcnf", "v2/control.xcnf",
    "v3/control.xcnf", "v3/public.xcnf",
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


frozen = json.loads((HERE / "archive_protocol.json").read_text())
assert frozen["status"] == "FROZEN_BEFORE_N41_LINKED_THREE_ATTEMPT_ARCHIVE"
assert frozen["archive_source_sha256"] == sha(Path(__file__))
assert frozen["raw_sha256"] == {name: sha(HERE / name) for name in FORMULAS}
receipts = {}
for name in FORMULAS:
    raw, packed = HERE / name, HERE / (name + ".gz")
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
    assert digest.hexdigest() == sha(raw)
    assert size == raw.stat().st_size
    receipts[name] = {"raw_sha256": digest.hexdigest(), "raw_bytes": size,
                      "gzip_sha256": sha(packed),
                      "gzip_bytes": packed.stat().st_size}
with (HERE / "archive_result.json").open("x") as stream:
    json.dump({"status": "PASS_N41_LINKED_THREE_ATTEMPT_XCNF_ARCHIVE",
               "files": receipts,
               "archive_protocol_sha256": sha(HERE / "archive_protocol.json")},
              stream, sort_keys=True, indent=2)
    stream.write("\n")
print("PASS_N41_LINKED_THREE_ATTEMPT_XCNF_ARCHIVE", flush=True)
