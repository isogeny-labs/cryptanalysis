"""Read-only custody check for the complete N41 three-code census."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
PREVIOUS = EXP / "n41_sixpair_code_propagation_20261115"
SOURCE = EXP / "n41_sixpair_shared_target_20261017"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = json.loads((HERE / "protocol.json").read_text())
    r = json.loads((HERE / "result.json").read_text())
    ap = json.loads((HERE / "audit_protocol.json").read_text())
    a = json.loads((HERE / "audit_result.json").read_text())
    sources = {"run": HERE / "run.py", "propagator": PREVIOUS / "screen.py",
               "xcnf": SOURCE / "public.xcnf", "join_input": SOURCE / "join_input.tsv",
               "witness": SOURCE / "join_audit_result.json"}
    assert all(sha(path) == p["source_sha256"][key] for key, path in sources.items())
    assert r["status"] == "COMPLETE_THREE_CODE_PROPAGATION"
    assert r["protocol_sha256"] == sha(HERE / "protocol.json")
    assert r["rows_sha256"] == sha(HERE / "rows.jsonl")
    assert r["completed"] == r["expected"] == 64000
    rows = [json.loads(line) for line in (HERE / "rows.jsonl").read_text().splitlines()]
    assert len(rows) == 64000
    assert sum(x["status"] == "CONFLICT" for x in rows) == r["conflicts"]
    assert sum(not x["source_valid"] for x in rows) == r["source_invalid"]
    assert sum(x["status"] == "CONFLICT" and x["source_valid"] for x in rows) == r["source_valid_conflicts"]
    assert r["witness_open"] and r["witness_codes"] == [6, 100, 97]
    assert any(x["codes"] == r["witness_codes"] and x["status"] == "OPEN" for x in rows)
    audit_sources = {"audit": HERE / "audit.py",
                     "reference_full_scan": PREVIOUS / "audit.py",
                     "join_input": SOURCE / "join_input.tsv",
                     "rows": HERE / "rows.jsonl", "result": HERE / "result.json",
                     "xcnf": SOURCE / "public.xcnf"}
    assert all(sha(path) == ap["sha256"][key] for key, path in audit_sources.items())
    assert a["protocol_sha256"] == sha(HERE / "audit_protocol.json")
    assert a["status"] == "PASS_SOURCE_CENSUS_AND_FULL_SCAN_SAMPLE"
    assert a["rows_checked_for_source_validity"] == 64000
    assert a["source_invalid"] == r["source_invalid"]
    assert a["source_valid_conflicts"] == r["source_valid_conflicts"]
    assert len(a["replay"]) == a["full_scan_replay_count"]
    for item in a["replay"]:
        row = rows[item["row_index"]]
        assert item["codes"] == row["codes"] and item["status"] == row["status"]
        if item["status"] == "OPEN":
            assert item["assigned_variables"] == row["assigned_variables"]
    print("PASS_N41_THREE_CODE_PROPAGATION_CUSTODY")


if __name__ == "__main__":
    main()
