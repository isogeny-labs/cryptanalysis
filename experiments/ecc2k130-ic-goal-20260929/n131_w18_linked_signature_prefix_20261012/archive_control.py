"""Archive the frozen constructed XCNF and verify byte replay."""

import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAT = HERE / "sat"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unpacked_hash(path):
    digest = hashlib.sha256()
    count = 0
    with gzip.open(path, "rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            count += len(chunk)
    return digest.hexdigest(), count


frozen = json.loads((HERE / "archive_protocol.json").read_text())
control = json.loads((SAT / "control_result.json").read_text())
assert frozen["sha256"]["source"] == sha(Path(__file__))
assert frozen["sha256"]["sat_protocol"] == sha(SAT / "protocol.json")
assert frozen["sha256"]["control"] == sha(SAT / "control_result.json")
raw = SAT / "control.xcnf"
packed = SAT / "control.xcnf.gz"
assert sha(raw) == control["formula"]["xcnf_sha256"]
assert raw.stat().st_size == control["formula"]["xcnf_bytes"]
with raw.open("rb") as source, packed.open("xb") as destination:
    with gzip.GzipFile(filename="", mode="wb", fileobj=destination,
                       compresslevel=3, mtime=0) as stream:
        while chunk := source.read(1024 * 1024):
            stream.write(chunk)
digest, size = unpacked_hash(packed)
assert digest == sha(raw) and size == raw.stat().st_size
result = {
    "status": "PASS_SIGNATURE_CONTROL_XCNF_GZIP_BYTE_REPLAY",
    "raw_sha256": digest,
    "raw_bytes": size,
    "gzip_sha256": sha(packed),
    "gzip_bytes": packed.stat().st_size,
    "archive_protocol_sha256": sha(HERE / "archive_protocol.json"),
}
with (HERE / "archive_receipt.json").open("x") as stream:
    json.dump(result, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(result["status"], result["gzip_bytes"])
