"""Archive the frozen ordinary XCNF with reversible byte evidence."""

import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAT = HERE / "sat"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


frozen = json.loads((HERE / "query_archive_protocol.json").read_text())
assert frozen["sha256"]["source"] == sha(Path(__file__))
assert frozen["sha256"]["query"] == sha(SAT / "query_result.json")
assert frozen["sha256"]["terminal_audit"] == sha(HERE / "query_audit_result.json")
query = json.loads((SAT / "query_result.json").read_text())
raw = SAT / "ordinary.xcnf"
packed = SAT / "ordinary.xcnf.gz"
assert sha(raw) == query["formula"]["xcnf_sha256"]
assert raw.stat().st_size == query["formula"]["xcnf_bytes"]
with raw.open("rb") as source, packed.open("xb") as destination:
    with gzip.GzipFile(filename="", mode="wb", fileobj=destination,
                       compresslevel=3, mtime=0) as stream:
        while True:
            chunk = source.read(1024 * 1024)
            if not chunk:
                break
            stream.write(chunk)
digest = hashlib.sha256()
size = 0
with gzip.open(packed, "rb") as stream:
    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            break
        digest.update(chunk)
        size += len(chunk)
assert digest.hexdigest() == sha(raw) and size == raw.stat().st_size
result = {
    "status": "PASS_SIGNATURE_PUBLIC_XCNF_GZIP_BYTE_REPLAY",
    "raw_sha256": digest.hexdigest(),
    "raw_bytes": size,
    "gzip_sha256": sha(packed),
    "gzip_bytes": packed.stat().st_size,
    "query_archive_protocol_sha256": sha(HERE / "query_archive_protocol.json"),
}
with (HERE / "query_archive_receipt.json").open("x") as stream:
    json.dump(result, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(result["status"], result["gzip_bytes"])
