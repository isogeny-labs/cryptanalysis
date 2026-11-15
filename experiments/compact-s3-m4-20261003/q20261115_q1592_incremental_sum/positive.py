#!/usr/bin/env python3
"""Amended positive-witness replay for Q1592's incremental kernel."""

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
Q1461 = PARENT / "q1461_sparse_sum_inverse"
Q1420 = PARENT / "q1420_root_theory"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")


def inputs():
    files = {"source": HERE / "positive.py", "parent_protocol": HERE / "protocol.json",
             "baseline_binary": HERE / "baseline_probe", "candidate_binary": HERE / "probe"}
    for n in (53, 83):
        files[f"n{n}_controls"] = Q1461 / f"n{n}_inputs.txt"
        files[f"n{n}_field"] = Q1420 / f"n{n}_field.txt"
    return files


def freeze():
    assert not (HERE / "positive_protocol.json").exists()
    save(HERE / "positive_protocol.json", {
        "proposal_id": "Q1592", "candidate_id": None, "run_id": None,
        "isogeny": "none", "input_sha256": {k: sha(v) for k, v in inputs().items()},
        "selected_rows": "first line of each archived Q1461 input, n53_planted and n83_planted",
        "sum_cap": 16384, "pair_cap": 100000,
        "gate": "Each arm equals direct enumeration and returns the same nonempty witness pairs",
    })


def checked():
    protocol = json.loads((HERE / "positive_protocol.json").read_text())
    assert all(sha(path) == protocol["input_sha256"][key]
               for key, path in inputs().items())
    return protocol


def run():
    protocol = checked()
    assert not (HERE / "positive_result.json").exists()
    cells = {}
    for n, weight in ((53, 4), (83, 6)):
        line = (Q1461 / f"n{n}_inputs.txt").read_text().splitlines()[0] + "\n"
        arms = {}
        for name, binary in (("baseline", HERE / "baseline_probe"),
                             ("incremental", HERE / "probe")):
            command = [str(binary), str(Q1420 / f"n{n}_field.txt"),
                       str(weight), str(protocol["sum_cap"]),
                       str(protocol["pair_cap"])]
            result = subprocess.run(command, input=line, text=True,
                                    capture_output=True, check=True, timeout=60)
            assert not result.stderr
            raw = HERE / f"n{n}_positive_{name}.jsonl"
            raw.write_text(result.stdout)
            rows = [json.loads(row) for row in result.stdout.splitlines()]
            assert len(rows) == 2 and rows[1]["kind"] == "state"
            assert rows[1]["verified_pairs"] > 0
            arms[name] = {"command": command, "raw_sha256": sha(raw),
                          "setup": rows[0], "state": rows[1]}
        ignored = {"basis_xors", "kernel_wall_ns_exploratory",
                   "direct_wall_ns_exploratory"}
        assert {k: v for k, v in arms["baseline"]["state"].items()
                if k not in ignored} == {k: v for k, v in
                arms["incremental"]["state"].items() if k not in ignored}
        cells[str(n)] = arms
    save(HERE / "positive_result.json", {
        "proposal_id": "Q1592", "protocol_sha256": sha(HERE / "positive_protocol.json"),
        "cells": cells, "status": "positive_witness_pair_sets_equal",
    })
    print(json.dumps({n: x["incremental"]["state"]["verified_pairs"]
                      for n, x in cells.items()}))


def audit():
    checked()
    result = json.loads((HERE / "positive_result.json").read_text())
    assert result["protocol_sha256"] == sha(HERE / "positive_protocol.json")
    for n, arms in result["cells"].items():
        for name, row in arms.items():
            assert row["raw_sha256"] == sha(HERE / f"n{n}_positive_{name}.jsonl")
            assert row["state"]["verified_pairs"] > 0
    print(json.dumps({"status": "passed", "proposal_id": "Q1592"}))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "run", "audit"))
    args = parser.parse_args()
    {"freeze": freeze, "run": run, "audit": audit}[args.mode]()
