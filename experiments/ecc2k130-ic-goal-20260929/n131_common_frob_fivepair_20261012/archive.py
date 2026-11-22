"""Byte-preserving archive of both N131 five-pair XCNFs."""

import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = ("control.xcnf", "public.xcnf")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    protocol = json.loads((HERE / "archive_protocol.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_XCNF_ARCHIVE"
    assert protocol["source_sha256"] == sha((HERE / "archive.py").read_bytes())
    assert protocol["input_sha256"] == {
        name: sha((HERE / name).read_bytes()) for name in INPUTS}
    result = {}
    for name in INPUTS:
        raw = (HERE / name).read_bytes()
        packed = gzip.compress(raw, compresslevel=9, mtime=0)
        output = HERE / (name + ".gz")
        with output.open("xb") as stream:
            stream.write(packed)
        assert gzip.decompress(output.read_bytes()) == raw
        result[name] = {"raw_sha256": sha(raw), "raw_bytes": len(raw),
                        "gzip_sha256": sha(packed), "gzip_bytes": len(packed)}
    with (HERE / "archive_result.json").open("x") as out:
        json.dump({"status": "PASS_BYTE_REPLAY_XCNF_ARCHIVE",
                   "protocol_sha256": sha((HERE / "archive_protocol.json").read_bytes()),
                   "files": result}, out, sort_keys=True, indent=2)
        out.write("\n")
    for name in INPUTS:
        (HERE / name).unlink()
    print("PASS_BYTE_REPLAY_XCNF_ARCHIVE", len(INPUTS))


if __name__ == "__main__":
    main()
