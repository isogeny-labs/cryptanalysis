#!/usr/bin/env python3
"""Project CNF-private XOR variables while bounding each new row's width."""

import argparse
import hashlib
import heapq
import json
import time
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def scan(path):
    nvars = declared = None
    cnf_used = None
    cnf_count = 0
    rows = {}
    rhs = {}
    with path.open("rb") as source:
        for line in source:
            if not line.strip() or line.startswith(b"c"):
                continue
            if line.startswith(b"p "):
                fields = line.split()
                assert fields[:2] == [b"p", b"cnf"] and len(fields) == 4
                nvars, declared = map(int, fields[2:])
                cnf_used = bytearray(nvars + 1)
            elif line.startswith(b"x"):
                assert nvars is not None
                tokens = line[1:].split()
                assert tokens[-1] == b"0"
                literals = [int(token) for token in tokens[:-1]]
                variables = {abs(value) for value in literals}
                assert variables and len(variables) == len(literals)
                assert all(1 <= value <= nvars for value in variables)
                index = len(rows)
                rows[index] = variables
                rhs[index] = 1 ^ (sum(value < 0 for value in literals) & 1)
            else:
                assert nvars is not None
                tokens = line.split()
                assert tokens[-1] == b"0"
                for token in tokens[:-1]:
                    variable = abs(int(token))
                    assert 1 <= variable <= nvars
                    cnf_used[variable] = 1
                cnf_count += 1
    assert cnf_count + len(rows) == declared
    return nvars, cnf_count, cnf_used, rows, rhs


def project(cnf_used, rows, rhs, max_new_width):
    columns = {}
    for index, row in rows.items():
        for variable in row:
            if not cnf_used[variable]:
                columns.setdefault(variable, set()).add(index)
    private_count = len(columns)
    heap = [(len(members), variable) for variable, members in columns.items()]
    heapq.heapify(heap)
    pivots = []
    skipped_private = set()
    row_additions = 0
    widest = max(map(len, rows.values()))
    while heap:
        old_count, variable = heapq.heappop(heap)
        if variable in skipped_private:
            continue
        members = columns[variable]
        if not members or old_count != len(members):
            continue
        pivot_index = min(members, key=lambda i: (len(rows[i]), i))
        pivot_candidate = rows[pivot_index]
        if any(len(rows[target_index] ^ pivot_candidate) > max_new_width
               for target_index in members if target_index != pivot_index):
            skipped_private.add(variable)
            continue
        pivot_row = rows.pop(pivot_index)
        parity = rhs.pop(pivot_index)
        targets = tuple(members - {pivot_index})
        touched = [value for value in pivot_row if not cnf_used[value]]
        pivots.append((variable, tuple(sorted(pivot_row)), parity))
        for value in touched:
            columns[value].remove(pivot_index)
        for target_index in targets:
            target = rows[target_index]
            for value in pivot_row:
                if value in target:
                    target.remove(value)
                    if not cnf_used[value]:
                        columns[value].remove(target_index)
                else:
                    target.add(value)
                    if not cnf_used[value]:
                        columns[value].add(target_index)
            rhs[target_index] ^= parity
            widest = max(widest, len(target))
            row_additions += 1
        for value in touched:
            heapq.heappush(heap, (len(columns[value]), value))
    pivot_variables = {item[0] for item in pivots}
    free_private = sorted(variable for variable, members in columns.items()
                          if not members and variable not in pivot_variables)
    kept_private = sorted(variable for variable, members in columns.items()
                          if members)
    assert len(pivots) + len(free_private) + len(kept_private) == private_count
    assert all(columns[variable] for variable in kept_private)
    assert all(not columns[variable] for variable in pivot_variables)
    return pivots, free_private, kept_private, row_additions, widest


def write_projection(source, output, mapping_path, lift_path,
                     nvars, cnf_count, cnf_used, rows, rhs, pivots,
                     free_private):
    active = bytearray(cnf_used)
    for row in rows.values():
        for variable in row:
            active[variable] = 1
    new_to_old = [0] + [variable for variable in range(1, nvars + 1)
                        if active[variable]]
    old_to_new = [0] * (nvars + 1)
    for new, old in enumerate(new_to_old[1:], 1):
        old_to_new[old] = new
    with mapping_path.open("x") as stream:
        json.dump({"new_to_old": new_to_old,
                   "free_private": free_private}, stream,
                  separators=(",", ":"))
        stream.write("\n")
    with lift_path.open("x") as stream:
        for pivot, variables, parity in pivots:
            stream.write(json.dumps({"pivot": pivot, "variables": variables,
                                     "rhs": parity}, separators=(",", ":")) + "\n")
    residual_count = sum(bool(row) for row in rows.values())
    contradictions = sum(not row and rhs[index] == 1
                         for index, row in rows.items())
    with output.open("x") as destination:
        destination.write(f"p cnf {len(new_to_old)-1} "
                          f"{cnf_count+residual_count+contradictions}\n")
        emitted_cnf = 0
        with source.open() as original:
            for line in original:
                if not line.strip() or line.startswith(("c", "p ", "x")):
                    continue
                literals = [int(token) for token in line.split()]
                assert literals[-1] == 0
                mapped = [old_to_new[abs(value)] * (1 if value > 0 else -1)
                          for value in literals[:-1]]
                assert all(mapped)
                destination.write(" ".join(map(str, mapped)) + " 0\n")
                emitted_cnf += 1
        assert emitted_cnf == cnf_count
        for index, row in sorted(rows.items()):
            mapped = sorted(old_to_new[value] for value in row)
            if not mapped:
                if rhs[index]:
                    destination.write("0\n")
                continue
            destination.write(("x" if rhs[index] else "x-") +
                              str(mapped[0]) +
                              (" " + " ".join(map(str, mapped[1:]))
                               if len(mapped) > 1 else "") + " 0\n")
    return len(new_to_old) - 1, contradictions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-new-width", type=int, required=True)
    args = parser.parse_args()
    assert args.max_new_width > 0
    assert not args.output_dir.exists()
    assert sha(args.input) == args.expected_sha256
    assert json.loads(args.runtime.read_text())["status"] == "verified"
    args.output_dir.mkdir(parents=True)
    started = time.perf_counter()
    nvars, cnf_count, cnf_used, rows, rhs = scan(args.input)
    original_xors = len(rows)
    pivots, free_private, kept_private, additions, widest = project(
        cnf_used, rows, rhs, args.max_new_width)
    residual_xors = sum(bool(row) for row in rows.values())
    projected = args.output_dir / "projected.xcnf"
    mapping = args.output_dir / "variable_map.json"
    lift = args.output_dir / "lift_rows.jsonl"
    output_vars, contradictions = write_projection(
        args.input, projected, mapping, lift, nvars, cnf_count,
        cnf_used, rows, rhs, pivots, free_private)
    result = {
        "kind": "cnf_private_xor_projection",
        "status": "PASS",
        "original_variables": nvars,
        "projected_variables": output_vars,
        "original_cnf_clauses": cnf_count,
        "original_xor_rows": original_xors,
        "projected_xor_rows": residual_xors,
        "private_pivots": len(pivots),
        "private_variables_kept": len(kept_private),
        "free_private_variables": len(free_private),
        "max_new_width": args.max_new_width,
        "projected_xor_literals": sum(map(len, rows.values())),
        "projected_contradictions": contradictions,
        "row_additions": additions,
        "widest_intermediate_row": widest,
        "projected_xcnf_bytes": projected.stat().st_size,
        "projection_wall_seconds": time.perf_counter() - started,
        "source_sha256": {
            "input_xcnf": args.expected_sha256,
            "projected_xcnf": sha(projected),
            "variable_map": sha(mapping),
            "lift_rows": sha(lift),
            "runtime": sha(args.runtime),
            "script": sha(Path(__file__)),
        },
    }
    (args.output_dir / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: result[key] for key in
                      ("status", "original_xor_rows", "projected_xor_rows",
                       "projected_variables", "projected_xcnf_bytes")}))


if __name__ == "__main__":
    main()
