#!/usr/bin/env python3
"""Independent raw-record audit of Q1592 paired and positive replays."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")


def freeze():
    assert not (HERE / "audit_protocol.json").exists()
    save(HERE / "audit_protocol.json", {
        "proposal_id": "Q1592", "audit_source_sha256": sha(Path(__file__)),
        "result_sha256": sha(HERE / "result.json"),
        "positive_result_sha256": sha(HERE / "positive_result.json"),
        "main_protocol_sha256": sha(HERE / "protocol.json"),
        "positive_protocol_sha256": sha(HERE / "positive_protocol.json"),
        "gate": "Raw paired state equality, positive witnesses, and record digests",
    })


def check():
    protocol = json.loads((HERE / "audit_protocol.json").read_text())
    for key, filename in (("audit_source_sha256", "audit.py"),
                          ("result_sha256", "result.json"),
                          ("positive_result_sha256", "positive_result.json"),
                          ("main_protocol_sha256", "protocol.json"),
                          ("positive_protocol_sha256", "positive_protocol.json")):
        assert sha(HERE / filename) == protocol[key]
    result = json.loads((HERE / "result.json").read_text())
    positive = json.loads((HERE / "positive_result.json").read_text())
    assert result["complete_n131_log2_work"] is None
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert positive["protocol_sha256"] == sha(HERE / "positive_protocol.json")
    comparisons = 0
    ignored = {"basis_xors", "kernel_wall_ns_exploratory",
               "direct_wall_ns_exploratory"}
    for n in (53, 83):
        cell = result["cells"][str(n)]
        for repetition in range(1, 8):
            raw = {}
            for arm in ("baseline", "incremental"):
                summary = cell["arms"][arm][repetition - 1]
                path = HERE / f"n{n}_r{repetition}_{arm}.jsonl"
                assert sha(path) == summary["raw_sha256"]
                rows = [json.loads(line) for line in path.read_text().splitlines()]
                assert len(rows) == 17 and rows[0] == summary["setup"]
                states = rows[1:]
                assert [row["state_index"] for row in states] == list(range(16))
                assert sum(x["basis_xors"] for x in states) == summary["basis_xors"]
                assert sum(x["elimination_xors"] for x in states) == summary["elimination_xors"]
                assert sum(x["verified_pairs"] for x in states) == 0
                assert sum(x["kernel_wall_ns_exploratory"] for x in states) == summary["kernel_wall_ns"]
                raw[arm] = states
            for a, b in zip(raw["baseline"], raw["incremental"]):
                assert {k: v for k, v in a.items() if k not in ignored} == {
                    k: v for k, v in b.items() if k not in ignored}
                comparisons += 1
        controls = {}
        for arm in ("baseline", "incremental"):
            summary = positive["cells"][str(n)][arm]
            path = HERE / f"n{n}_positive_{arm}.jsonl"
            assert sha(path) == summary["raw_sha256"]
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            assert len(rows) == 2 and rows[1] == summary["state"]
            assert rows[1]["verified_pairs"] == len(rows[1]["witness_pairs"]) == 1
            controls[arm] = rows[1]
        assert {k: v for k, v in controls["baseline"].items()
                if k not in ignored} == {k: v for k, v in
                controls["incremental"].items() if k not in ignored}
    save(HERE / "audit_result.json", {
        "proposal_id": "Q1592", "status": "passed",
        "ordinary_state_comparisons": comparisons,
        "positive_witness_comparisons": 2,
        "audit_protocol_sha256": sha(HERE / "audit_protocol.json"),
    })
    print(json.dumps({"status": "passed", "ordinary_state_comparisons": comparisons,
                      "positive_witness_comparisons": 2}))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "check"))
    args = parser.parse_args()
    {"freeze": freeze, "check": check}[args.mode]()
