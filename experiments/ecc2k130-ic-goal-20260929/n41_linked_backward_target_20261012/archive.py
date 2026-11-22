"""Archive every attempted XCNF with byte-replay receipts."""

import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = ("v2/control.xcnf", "v3/control.xcnf",
          "v4/control.xcnf", "v4/public.xcnf")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    protocol = json.loads((HERE / "archive_protocol.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_ARCHIVE"
    assert protocol["archive_source_sha256"] == sha((HERE / "archive.py").read_bytes())
    assert protocol["inputs"] == {name: sha((HERE / name).read_bytes()) for name in INPUTS}
    result = {}
    for name in INPUTS:
        data = (HERE / name).read_bytes()
        archived = gzip.compress(data, compresslevel=9, mtime=0)
        output = HERE / (name + ".gz")
        with output.open("xb") as stream:
            stream.write(archived)
        assert gzip.decompress(output.read_bytes()) == data
        result[name] = {"raw_sha256": sha(data), "raw_bytes": len(data),
                        "gzip_sha256": sha(archived), "gzip_bytes": len(archived)}
    with (HERE / "archive_result.json").open("x") as stream:
        json.dump({"status": "BYTE_REPLAY_PASS", "files": result,
                   "protocol_sha256": sha((HERE / "archive_protocol.json").read_bytes())},
                  stream, sort_keys=True, indent=2)
        stream.write("\n")
    for name in INPUTS:
        (HERE / name).unlink()
    print("BYTE_REPLAY_PASS", len(INPUTS))


if __name__ == "__main__":
    main()
