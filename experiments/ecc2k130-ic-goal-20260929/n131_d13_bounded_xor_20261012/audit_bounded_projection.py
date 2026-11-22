#!/usr/bin/env python3
"""Replay a bounded XOR pivot certificate and check a planted model."""

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def parse(path):
    header = None
    cnf = []
    xor = []
    for raw in path.open("rt", encoding="ascii"):
        if not raw.strip() or raw.startswith("c"):
            continue
        if raw.startswith("p "):
            fields = raw.split()
            assert header is None and fields[:2] == ["p", "cnf"]
            header = tuple(map(int, fields[2:]))
            continue
        is_xor = raw.startswith("x")
        fields = raw[1:].split() if is_xor else raw.split()
        assert fields[-1] == "0"
        literals = tuple(map(int, fields[:-1]))
        if is_xor:
            assert literals and len({abs(x) for x in literals}) == len(literals)
            xor.append((set(map(abs, literals)),
                        1 ^ (sum(x < 0 for x in literals) & 1)))
        else:
            cnf.append(literals)
    assert header is not None and len(cnf) + len(xor) == header[1]
    return header, cnf, xor


def save_model(path, values):
    with path.open("x") as stream:
        stream.write("s SATISFIABLE\n")
        for index in range(1, len(values), 1000):
            stream.write("v " + " ".join(
                str(i if values[i] else -i)
                for i in range(index, min(index + 1000, len(values)))) + " 0\n")


def audit(source, output_dir, control_model):
    result_path = output_dir / "result.json"
    result = json.loads(result_path.read_text())
    assert result["status"] == "PASS"
    hashes = result["source_sha256"]
    projected_path = output_dir / "projected.xcnf"
    mapping_path = output_dir / "variable_map.json"
    certificate_path = output_dir / "lift_rows.jsonl"
    for key, path in (("input_xcnf", source), ("projected_xcnf", projected_path),
                      ("variable_map", mapping_path), ("lift_rows", certificate_path)):
        assert sha(path) == hashes[key]
    (original_n, _), original_cnf, original_xor = parse(source)
    (projected_n, _), projected_cnf, projected_xor = parse(projected_path)
    mapping = json.loads(mapping_path.read_text())
    new_to_old = mapping["new_to_old"]
    assert len(new_to_old) == projected_n + 1 and new_to_old[0] == 0
    assert new_to_old[1:] == sorted(set(new_to_old[1:]))
    old_to_new = {old: new for new, old in enumerate(new_to_old) if new}
    assert len(original_cnf) == len(projected_cnf)
    for original, projected in zip(original_cnf, projected_cnf):
        assert tuple((1 if x > 0 else -1) * old_to_new[abs(x)]
                     for x in original) == projected

    cnf_used = {abs(x) for clause in original_cnf for x in clause}
    private = {v for row, _ in original_xor for v in row if v not in cnf_used}
    rows = {i: (set(row), rhs) for i, (row, rhs) in enumerate(original_xor)}
    columns = {v: set() for v in private}
    for index, (row, _) in rows.items():
        for variable in row & private:
            columns[variable].add(index)
    pivot_order = {}
    additions = 0
    for line in certificate_path.open():
        item = json.loads(line)
        variable = item["pivot"]
        pivot = set(item["variables"])
        parity = item["rhs"]
        assert variable in private and variable in pivot
        assert variable not in pivot_order and len(pivot) == len(item["variables"])
        candidates = [i for i in columns[variable]
                      if rows[i] == (pivot, parity)]
        assert candidates, ("missing certified pivot", variable)
        pivot_index = min(candidates)
        targets = tuple(columns[variable] - {pivot_index})
        for target_index in targets:
            target, old_rhs = rows[target_index]
            replacement = target.symmetric_difference(pivot)
            assert len(replacement) <= result["max_new_width"]
            for changed in (target ^ replacement) & private:
                if changed in target:
                    columns[changed].remove(target_index)
                else:
                    columns[changed].add(target_index)
            rows[target_index] = (replacement, old_rhs ^ parity)
            additions += 1
        for changed in pivot & private:
            columns[changed].remove(pivot_index)
        del rows[pivot_index]
        pivot_order[variable] = len(pivot_order)
    assert additions == result["row_additions"]
    assert len(pivot_order) == result["private_pivots"]
    expected = Counter((tuple(sorted(row)), rhs) for row, rhs in rows.values()
                       if row or rhs)
    actual = Counter((tuple(sorted(new_to_old[v] for v in row)), rhs)
                     for row, rhs in projected_xor)
    assert expected == actual
    assert len(rows) == result["original_xor_rows"] - len(pivot_order)
    assert sum(len(row) for row, _ in rows.values()) == result["projected_xor_literals"]
    assert set(range(1, original_n + 1)) == (set(new_to_old[1:]) |
                                                set(pivot_order) |
                                                set(mapping["free_private"]))
    assert not (set(new_to_old[1:]) & set(pivot_order))
    for index, line in enumerate(certificate_path.open()):
        item = json.loads(line)
        assert all(v == item["pivot"] or v in old_to_new or
                   pivot_order[v] > index for v in item["variables"])

    receipt = {"status": "PASS", "kind": "independent_bounded_xor_certificate_replay",
               "pivots": len(pivot_order), "row_additions": additions,
               "residual_xors": len(projected_xor),
               "source_sha256": {"original": sha(source), "projected": sha(projected_path),
                                 "certificate": sha(certificate_path),
                                 "auditor": sha(Path(__file__))}}
    if control_model is not None:
        verifier_dir = source.parent.parent / "m16_prefix_audit_20261006"
        sys.path.insert(0, str(verifier_dir))
        import verify_xcnf_model as verifier
        original_values = verifier.model_from_stdout(control_model, original_n)
        assert verifier.verify(source, control_model)["status"] == "PASS"
        projected_values = [None] + [original_values[old] for old in new_to_old[1:]]
        projected_model = output_dir / "projected_control_model.stdout.txt"
        save_model(projected_model, projected_values)
        receipt["projected_control"] = verifier.verify(projected_path, projected_model)
        lifted = [None] * (original_n + 1)
        for new, old in enumerate(new_to_old[1:], 1):
            lifted[old] = projected_values[new]
        for variable in mapping["free_private"]:
            lifted[variable] = False
        for line in reversed(certificate_path.read_text().splitlines()):
            item = json.loads(line)
            value = item["rhs"]
            for variable in item["variables"]:
                if variable != item["pivot"]:
                    assert lifted[variable] is not None
                    value ^= lifted[variable]
            lifted[item["pivot"]] = bool(value)
        assert all(v is not None for v in lifted[1:])
        lifted_model = output_dir / "lifted_control_model.stdout.txt"
        save_model(lifted_model, lifted)
        receipt["lifted_control"] = verifier.verify(source, lifted_model)
        receipt["lift_matches_frozen_model"] = (lifted == original_values)
        receipt["source_sha256"]["control_model"] = sha(control_model)
        receipt["source_sha256"]["projected_control_model"] = sha(projected_model)
        receipt["source_sha256"]["lifted_control_model"] = sha(lifted_model)
    receipt_path = output_dir / "independent_audit.json"
    assert not receipt_path.exists()
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "PASS", "pivots": len(pivot_order),
                      "residual_xors": len(projected_xor),
                      "control": control_model is not None}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--control-model", type=Path)
    args = parser.parse_args()
    audit(args.source, args.output_dir, args.control_model)
