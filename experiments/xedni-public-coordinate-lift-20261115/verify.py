"""Verify hashes, raw rows, and independent audit status."""

import gzip
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "xedni-large-order-admission-20261115" / "result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    audit = json.loads((HERE / "audit.json").read_text())
    assert result["status"] == audit["status"] == "PASS"
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["source_sha256"] == sha(HERE / "run.py")
    assert result["input_sha256"] == sha(INPUT) == \
        protocol["input_selection_result_sha256"]
    assert audit["fields"] == len(result["fields"]) == 8
    for field in result["fields"]:
        path = HERE / field["rows_path"]
        assert sha(path) == field["rows_sha256"]
        with gzip.open(path, "rt") as stream:
            assert sum(1 for _ in stream) == field["queries"]
    assert result["totals"]["queries"] == audit["queries"] == 3318
    assert result["totals"]["candidate_x_probes"] == \
        audit["candidate_x_probes"] == 69230
    assert result["total_rational_relation_hits"] == \
        audit["rational_relation_hits"] == 14
    assert not (HERE / "run.stderr").read_bytes()
    assert not (HERE / "audit.stderr").read_bytes()
    print(json.dumps({"schema": "xedni-public-coordinate-lift-verify-v1",
                      "status": "PASS", "fields": 8,
                      "queries": 3318, "candidate_x_probes": 69230,
                      "rational_relation_hits": 14}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
