"""Archive both frozen XCNF files as deterministic gzip with byte replay."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def uncompressed_digest(path):
    digest = hashlib.sha256()
    size = 0
    with gzip.open(path, "rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def archive(directory):
    directory = Path(directory).resolve()
    control = json.loads((directory / "control_result.json").read_text())
    query = json.loads((directory / "query_result.json").read_text())
    profiles = {"control": control["formula"], "ordinary": query["formula"]}
    receipt = {"status": "PASS_FROZEN_XCNF_GZIP_BYTE_REPLAY",
               "protocol_sha256": sha(directory / "protocol.json"), "formulas": {}}
    for name, profile in profiles.items():
        raw = directory / f"{name}.xcnf"
        packed = directory / f"{name}.xcnf.gz"
        assert raw.is_file() and not packed.exists()
        assert sha(raw) == profile["xcnf_sha256"]
        assert raw.stat().st_size == profile["xcnf_bytes"]
        with raw.open("rb") as source, packed.open("xb") as target:
            with gzip.GzipFile(filename="", mode="wb", fileobj=target,
                               compresslevel=9, mtime=0) as stream:
                while chunk := source.read(1024 * 1024):
                    stream.write(chunk)
        replay_digest, replay_size = uncompressed_digest(packed)
        assert replay_digest == profile["xcnf_sha256"]
        assert replay_size == profile["xcnf_bytes"]
        receipt["formulas"][name] = {
            "raw_sha256": replay_digest, "raw_bytes": replay_size,
            "gzip_sha256": sha(packed), "gzip_bytes": packed.stat().st_size}
    with (directory / "archive_receipt.json").open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(receipt["status"], directory.name,
          {key: value["gzip_bytes"] for key, value in receipt["formulas"].items()})


def verify(directory):
    directory = Path(directory).resolve()
    receipt = json.loads((directory / "archive_receipt.json").read_text())
    control = json.loads((directory / "control_result.json").read_text())
    query = json.loads((directory / "query_result.json").read_text())
    assert receipt["status"] == "PASS_FROZEN_XCNF_GZIP_BYTE_REPLAY"
    assert receipt["protocol_sha256"] == sha(directory / "protocol.json")
    for name, profile in (("control", control["formula"]),
                          ("ordinary", query["formula"])):
        packed = directory / f"{name}.xcnf.gz"
        row = receipt["formulas"][name]
        assert sha(packed) == row["gzip_sha256"]
        assert packed.stat().st_size == row["gzip_bytes"]
        digest, size = uncompressed_digest(packed)
        assert digest == row["raw_sha256"] == profile["xcnf_sha256"]
        assert size == row["raw_bytes"] == profile["xcnf_bytes"]
    print("PASS_ARCHIVED_XCNF_REPLAY", directory.name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    (verify if args.verify else archive)(args.directory)
