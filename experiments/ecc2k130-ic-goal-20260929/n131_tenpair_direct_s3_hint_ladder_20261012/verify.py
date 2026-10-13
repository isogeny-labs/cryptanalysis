"""Independent byte and terminal audit of the frozen upper-node ladder."""
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return sha_bytes(path.read_bytes())


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    aggregate = json.loads((HERE / "aggregate.json").read_text())
    build = json.loads((HERE / "build.json").read_text())
    assert aggregate["protocol_sha256"] == sha(HERE / "protocol.json")
    assert build["status"] == "PASS_EXACT_DIRECT_S3_REBUILD_AND_ASSIGNMENT"
    assert build["assignment_check"] == protocol["assignment_check"]
    assert len(aggregate["arms"]) == len(protocol["arms"]) == 4
    checks = []
    for expected, row in zip(protocol["arms"], aggregate["arms"]):
        name = expected["name"]
        assert row["name"] == name and row["upper_indexes"] == expected["upper_indexes"]
        receipt = json.loads((HERE / (name + ".json")).read_text())
        assert receipt["status"] == row["status"] == "PARENT_TIME_CAP"
        assert receipt["formula"]["unit_clauses"] == 1490 + 131 * len(expected["upper_indexes"])
        assert receipt["model_check"] is None and receipt["terminal_lines"] == []
        packed = HERE / (name + ".xcnf.gz")
        raw = gzip.open(packed, "rb").read()
        assert sha_bytes(raw) == row["archive"]["raw_sha256"] == receipt["formula"]["sha256"]
        assert len(raw) == row["archive"]["raw_bytes"] == receipt["formula"]["bytes"]
        assert sha(packed) == row["archive"]["gzip_sha256"]
        assert sha(HERE / (name + ".stdout.txt")) == receipt["stdout_sha256"]
        assert sha(HERE / (name + ".stderr.txt")) == receipt["stderr_sha256"]
        checks.append({"name": name, "status": receipt["status"],
                       "raw_sha256": sha_bytes(raw), "restart_rows": receipt["restart_rows"]})
    result = {"status": "PASS_FROZEN_DIRECT_S3_HINT_LADDER_AUDIT",
              "protocol_sha256": sha(HERE / "protocol.json"), "checks": checks}
    (HERE / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(result["status"], len(checks), flush=True)


if __name__ == "__main__":
    main()
