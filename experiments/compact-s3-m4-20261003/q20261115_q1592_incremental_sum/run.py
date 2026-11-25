#!/usr/bin/env python3
"""Freeze and replay Q1592's paired sparse-sum kernel screen."""

import hashlib
import json
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
Q1461 = PARENT / "q1461_sparse_sum_inverse"
Q1420 = PARENT / "q1420_root_theory"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def sources():
    fixed = {
        "design": HERE / "design.json",
        "driver": HERE / "run.py",
        "candidate_header": HERE / "incremental_sum.hpp",
        "candidate_probe_source": HERE / "probe.cpp",
        "candidate_binary": HERE / "probe",
        "baseline_header": Q1461 / "sparse_sum.hpp",
        "baseline_probe_source": Q1461 / "probe.cpp",
        "baseline_binary": HERE / "baseline_probe",
        "field_header": Q1420 / "root_field.hpp",
        "lift_header": PARENT / "q1422_leaf_lift_gate/lift_gate.hpp",
    }
    for n in (53, 83):
        fixed[f"n{n}_states"] = HERE / f"n{n}_states.txt"
        fixed[f"n{n}_field"] = Q1420 / f"n{n}_field.txt"
        fixed[f"n{n}_q1480_receipt"] = PARENT / "q1480_conditioned_join" / "runs" / f"n{n}_q1438_ordinary" / "receipt.json"
    return fixed


def freeze():
    path = HERE / "protocol.json"
    assert not path.exists()
    design = json.loads((HERE / "design.json").read_text())
    assert design["proposal_id"] == "Q1592"
    assert design["candidate_id"] is design["run_id"] is None
    assert design["isogeny"] == "none"
    commands = []
    for source, binary in ((Q1461 / "probe.cpp", HERE / "baseline_probe"),
                           (HERE / "probe.cpp", HERE / "probe")):
        command = ["c++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror",
                   str(source), "-o", str(binary)]
        subprocess.run(command, check=True)
        commands.append(command)
    for n in (53, 83):
        receipt = json.loads((PARENT / "q1480_conditioned_join" / "runs" /
            f"n{n}_q1438_ordinary" / "receipt.json").read_text())
        states = receipt["native_report"]["joint_rejection_snapshots"][:16]
        expected = [" ".join((f"n{n}_q1480_right", str(i), "1",
            row["second_mid_onb_hex"], row["leaf_fixed_mask_onb_hex"][2],
            row["leaf_ones_onb_hex"][2], row["leaf_fixed_mask_onb_hex"][3],
            row["leaf_ones_onb_hex"][3])) for i, row in enumerate(states)]
        assert (HERE / f"n{n}_states.txt").read_text() == "\n".join(expected) + "\n"
    save(path, {
        "proposal_id": "Q1592", "candidate_id": None, "run_id": None,
        "isogeny": "none", "source_sha256": {k: sha(v) for k, v in sources().items()},
        "build_commands": commands,
        "compiler_version": subprocess.run(["c++", "--version"], check=True,
            capture_output=True, text=True).stdout.splitlines()[0],
        "baseline_weight": {"53": 4, "83": 6},
        "sum_cap": design["sum_cap"], "pair_cap": design["pair_cap"],
        "repetitions": design["repetitions"],
        "claim_boundary": design["claim_boundary"],
    })


def checked():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert all(sha(path) == protocol["source_sha256"][key]
               for key, path in sources().items())
    return protocol


def run():
    protocol = checked()
    assert not (HERE / "result.json").exists()
    records = {}
    for n in (53, 83):
        cells = {"baseline": [], "incremental": []}
        input_text = (HERE / f"n{n}_states.txt").read_text()
        for repetition in range(protocol["repetitions"]):
            order = ("baseline", "incremental") if repetition % 2 == 0 else (
                "incremental", "baseline")
            paired = {}
            for arm in order:
                binary = HERE / ("baseline_probe" if arm == "baseline" else "probe")
                command = [str(binary), str(Q1420 / f"n{n}_field.txt"),
                           str(protocol["baseline_weight"][str(n)]),
                           str(protocol["sum_cap"]), str(protocol["pair_cap"])]
                completed = subprocess.run(command, input=input_text, text=True,
                    capture_output=True, timeout=300, check=True)
                raw = HERE / f"n{n}_r{repetition + 1}_{arm}.jsonl"
                raw.write_text(completed.stdout)
                assert not completed.stderr
                rows = [json.loads(line) for line in completed.stdout.splitlines()]
                assert len(rows) == 17 and rows[0]["kind"] == "setup"
                states = rows[1:]
                assert [x["state_index"] for x in states] == list(range(16))
                paired[arm] = states
                cells[arm].append({
                    "repetition": repetition + 1, "input_order": list(order),
                    "raw_sha256": sha(raw),
                    "setup": rows[0],
                    "basis_xors": sum(x["basis_xors"] for x in states),
                    "elimination_xors": sum(x["elimination_xors"] for x in states),
                    "kernel_mul": sum(x["kernel_mul_calls"] for x in states),
                    "kernel_sqr": sum(x["kernel_sqr_calls"] for x in states),
                    "kernel_inv": sum(x["kernel_inv_calls"] for x in states),
                    "kernel_wall_ns": sum(x["kernel_wall_ns_exploratory"]
                                          for x in states),
                    "direct_wall_ns": sum(x["direct_wall_ns_exploratory"]
                                          for x in states),
                    "verified_pairs": sum(x["verified_pairs"] for x in states),
                })
            for base, new in zip(paired["baseline"], paired["incremental"]):
                ignored = {"basis_xors", "kernel_wall_ns_exploratory",
                           "direct_wall_ns_exploratory"}
                assert {k: v for k, v in base.items() if k not in ignored} == {
                    k: v for k, v in new.items() if k not in ignored}
        records[str(n)] = {
            "arms": cells,
            "median_kernel_wall_ns": {arm: int(statistics.median(
                row["kernel_wall_ns"] for row in cells[arm]))
                for arm in cells},
            "basis_xors": {arm: cells[arm][0]["basis_xors"] for arm in cells},
            "statuses": "exact_pair_set_agreement; 16 ordinary states have zero verified pairs",
        }
    save(HERE / "result.json", {
        "proposal_id": "Q1592", "candidate_id": None, "run_id": None,
        "isogeny": "none", "protocol_sha256": sha(HERE / "protocol.json"),
        "cells": records, "complete_n131_log2_work": None,
    })
    print(json.dumps({n: {"basis_xors": x["basis_xors"],
                          "median_kernel_wall_ns": x["median_kernel_wall_ns"]}
                      for n, x in records.items()}, sort_keys=True))


def audit():
    checked()
    result = json.loads((HERE / "result.json").read_text())
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    for n, cell in result["cells"].items():
        for arm, rows in cell["arms"].items():
            assert len(rows) == 7
            assert len({x["basis_xors"] for x in rows}) == 1
            assert all(x["verified_pairs"] == 0 for x in rows)
            for row in rows:
                raw = HERE / f"n{n}_r{row['repetition']}_{arm}.jsonl"
                assert row["raw_sha256"] == sha(raw)
    print(json.dumps({"status": "passed", "proposal_id": "Q1592",
                      "state_comparisons": 2 * 7 * 16}))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "run", "audit"))
    args = parser.parse_args()
    {"freeze": freeze, "run": run, "audit": audit}[args.mode]()
