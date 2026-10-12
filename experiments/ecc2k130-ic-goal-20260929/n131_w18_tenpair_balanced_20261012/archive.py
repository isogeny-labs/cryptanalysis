"""Deterministic gzip archive and byte-level replay for the control XCNF."""

import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(stream):
    sha = hashlib.sha256()
    size = 0
    for block in iter(lambda: stream.read(1 << 20), b""):
        sha.update(block)
        size += len(block)
    return sha.hexdigest(), size


def verify():
    profile = json.loads((HERE / "control_result.json").read_text())["formula"]
    receipt = json.loads((HERE / "archive_receipt.json").read_text())
    packed = HERE / "control.xcnf.gz"
    with packed.open("rb") as stream:
        gz_sha, gz_size = digest(stream)
    with gzip.open(packed, "rb") as stream:
        raw_sha, raw_size = digest(stream)
    assert receipt == {"status": "PASS_TENPAIR_CONTROL_ARCHIVE",
                       "raw_sha256": raw_sha, "raw_bytes": raw_size,
                       "gzip_sha256": gz_sha, "gzip_bytes": gz_size}
    assert raw_sha == profile["xcnf_sha256"]
    assert raw_size == profile["xcnf_bytes"]
    print("PASS_TENPAIR_CONTROL_ARCHIVE", flush=True)


def archive():
    profile = json.loads((HERE / "control_result.json").read_text())["formula"]
    raw, packed = HERE / "control.xcnf", HERE / "control.xcnf.gz"
    assert raw.is_file() and not packed.exists()
    with raw.open("rb") as stream:
        raw_sha, raw_size = digest(stream)
    assert (raw_sha, raw_size) == (profile["xcnf_sha256"], profile["xcnf_bytes"])
    with raw.open("rb") as source, packed.open("xb") as target:
        with gzip.GzipFile(filename="", mode="wb", fileobj=target,
                           compresslevel=9, mtime=0) as output:
            for block in iter(lambda: source.read(1 << 20), b""):
                output.write(block)
    with packed.open("rb") as stream:
        gz_sha, gz_size = digest(stream)
    with (HERE / "archive_receipt.json").open("x") as stream:
        json.dump({"status": "PASS_TENPAIR_CONTROL_ARCHIVE",
                   "raw_sha256": raw_sha, "raw_bytes": raw_size,
                   "gzip_sha256": gz_sha, "gzip_bytes": gz_size},
                  stream, sort_keys=True, indent=2)
        stream.write("\n")
    verify()


if __name__ == "__main__":
    import sys
    {"archive": archive, "verify": verify}[sys.argv[1]]()
