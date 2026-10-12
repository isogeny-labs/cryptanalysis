"""Independently check every XCNF row and decode a fresh-target SAT model."""

import hashlib
import json
from pathlib import Path

import linear

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write("\n")


def main():
    solver = json.loads((HERE / "solver_result.json").read_text())
    assert solver["status"] == "SAT_PENDING_INDEPENDENT_REPLAY"
    build = json.loads((HERE / "ordinary_build_result.json").read_text())
    target = json.loads((HERE / "public_target.json").read_text())
    assert build["formula"]["xcnf_sha256"] == sha(HERE / "ordinary.xcnf")
    assert solver["stdout_sha256"] == sha(HERE / "solver.stdout.txt")
    lines = (HERE / "solver.stdout.txt").read_text().splitlines()
    assert "s SATISFIABLE" in lines
    assignment = {}
    for line in lines:
        if line.startswith("v "):
            for token in line.split()[1:]:
                literal = int(token)
                if literal:
                    assert abs(literal) not in assignment
                    assignment[abs(literal)] = literal > 0
    assert len(assignment) == build["formula"]["variables"]

    def value(literal):
        return assignment[abs(literal)] if literal > 0 else not assignment[abs(literal)]

    clauses = xors = bad_clauses = bad_xors = 0
    with (HERE / "ordinary.xcnf").open() as source:
        assert source.readline().split() == [
            "p", "cnf", str(len(assignment)),
            str(build["formula"]["clauses"] + build["formula"]["native_xor_rows"])]
        for line in source:
            parts = line.split()
            assert parts[-1] == "0"
            if parts[0].startswith("x"):
                positive = not parts[0].startswith("x-")
                first = int(parts[0][1:] if positive else parts[0][2:])
                parity = sum(value(literal) for literal in
                             [first] + [int(part) for part in parts[1:-1]]) & 1
                bad_xors += parity != positive
                xors += 1
            else:
                bad_clauses += not any(value(int(part)) for part in parts[:-1])
                clauses += 1
    assert clauses == build["formula"]["clauses"]
    assert xors == build["formula"]["native_xor_rows"]
    assert bad_clauses == bad_xors == 0

    circuit, wires = linear.build(target["raw_standard_reciprocal_x"])
    assert circuit.next_var - 1 == len(assignment)

    def decode(vector):
        return sum(int(assignment[wire]) << bit for bit, wire in enumerate(vector))

    seed, bits = linear.seven.seed_and_bits()
    codes = [decode(vector) for vector in wires["selectors"]]
    masks = [sum(((code >> index) & 1) << bit
                 for index, bit in enumerate(bits)) for code in codes]
    mask_pairs = [[mask, mask ^ seed] for mask in masks]
    table = {int(mask): int(column) for mask, column, shift in
             (line.split() for line in (linear.W20 / "support_w20.tsv").read_text().splitlines())}
    assert all(a in table and b in table and table[a] != table[b]
               for a, b in mask_pairs)
    columns = [[table[a], table[b]] for a, b in mask_pairs]
    flat = [column for pair in columns for column in pair]
    result = {"status": "PASS_W20_OUTPUT_LINEAR_XCNF_MODEL",
              "workload_id": target["workload_id"],
              "model_variables": len(assignment),
              "clauses_checked": clauses, "xor_rows_checked": xors,
              "failed_clauses": bad_clauses, "failed_xors": bad_xors,
              "source_mask_pairs": mask_pairs,
              "source_folded_columns": columns,
              "all_source_columns_distinct": len(set(flat)) == len(flat),
              "unrotated_pair_standard_reciprocals":
                  [decode(vector) for vector in wires["outputs"]],
              "output_inverse_witnesses":
                  [decode(vector) for vector in wires["output_inverse"]],
              "source_inverse_witnesses":
                  [[decode(vector) for vector in slot]
                   for slot in wires["inverse_witnesses"]],
              "intermediate_standard_reciprocals":
                  [decode(vector) for vector in wires["intermediates"]],
              "target_standard_reciprocal": target["raw_standard_reciprocal_x"],
              "source_sha256": {"audit": sha(__file__),
                                "formula": sha(HERE / "ordinary.xcnf"),
                                "solver_stdout": sha(HERE / "solver.stdout.txt"),
                                "target": sha(HERE / "public_target.json")}}
    save("model_audit_result.json", result)
    print("PASS_W20_OUTPUT_LINEAR_XCNF_MODEL", clauses, xors)


if __name__ == "__main__":
    main()
