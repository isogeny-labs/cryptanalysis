"""Independent terminal and full SAT-model replay for the 128 branch slices."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n41_allseed_fourpair_forward_20261012"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / "slice_protocol.json").read_text())
result = json.loads((HERE / "slice_result.json").read_text())
receipt = json.loads((HERE / "slice_audit.json").read_text())
build = json.loads((HERE / "build_result.json").read_text())
chart = json.loads((PARENT / "chart.json").read_text())
sage = json.loads((PARENT / "audit_result.json").read_text())
assert protocol["status"] == "FROZEN_BEFORE_ALL_PAIR_BRANCH_SLICES"
assert all(sha(path) == digest for path, digest in protocol["sources"].items())
assert result["status"] == "COMPLETE" and result["completed"] == result["total"] == 128
assert receipt["status"] == "PASS_FROZEN_BRANCH_SLICE_RECEIPT_AUDIT"
assert receipt["result_sha256"] == sha(HERE / "slice_result.json")
assert sage["status"] == "PASS_INDEPENDENT_N41_ALLSEED_FORWARD_CHART"
rows = [json.loads(line) for line in (HERE / "slice_results.jsonl").read_text().splitlines()]
assert len(rows) == 128 and len({row["index"] for row in rows}) == 128
wire_map = build["variants"]["all_pair"]["wire_map"]
models = []
for row in rows:
    lines = (HERE / f"slice_{row['index']:03}.stdout").read_text(errors="replace").splitlines()
    terminals = [line for line in lines if line.startswith("s ")]
    assert len(terminals) == 1 and terminals[0] == row["terminal"]
    assert row["stdout_sha256"] == sha(HERE / f"slice_{row['index']:03}.stdout")
    assert row["stderr_sha256"] == sha(HERE / f"slice_{row['index']:03}.stderr")
    if row["status"] == "UNSAT":
        assert row["terminal"] == "s UNSATISFIABLE" and row["stop_reason"] is None
        continue
    assert row["status"] == "SAT_PENDING_REPLAY" and row["terminal"] == "s SATISFIABLE"
    assignment = {}
    for line in lines:
        if line.startswith("v "):
            for word in line.split()[1:]:
                literal = int(word)
                if literal:
                    assert abs(literal) not in assignment
                    assignment[abs(literal)] = literal > 0
    with (HERE / "all_pair.xcnf").open() as stream:
        head = stream.readline().split()
        assert head[:2] == ["p", "cnf"]
        variables, expected_rows = map(int, head[2:])
        assert set(assignment) == set(range(1, variables + 1))
        cnf = xor = 0
        for line in stream:
            parts = line.split()
            is_xor = parts[0] == "x"
            lits = list(map(int, parts[1 if is_xor else 0:-1]))
            assert parts[-1] == "0" and lits
            values = [assignment[abs(lit)] == (lit > 0) for lit in lits]
            assert (sum(values) & 1) if is_xor else any(values)
            if is_xor:
                xor += 1
            else:
                cnf += 1
        assert cnf + xor == expected_rows
    masks = [sum(int(assignment[wire]) << bit for bit, wire in enumerate(bits))
             for bits in wire_map["mask_bits"]]
    branches = [int(assignment[wire]) for wire in wire_map["root_branches"]]
    assert masks == chart["masks"]
    assert branches == chart["root_branch_bits"]
    assert sum(bit << i for i, bit in enumerate(branches)) == row["index"]
    assert sage["root_links"] == 7 and sage["distinct_folded_columns"] == 8
    models.append({"index": row["index"], "variables": variables,
                   "cnf_clauses_checked": cnf, "native_xor_rows_checked": xor,
                   "masks": masks, "root_branch_bits": branches})
assert len(models) == 1 and models[0]["index"] == result["positive_index"]
output = {"status": "PASS_INDEPENDENT_128_SLICE_TERMINAL_AND_SAT_MODEL_AUDIT",
          "completed": len(rows), "solver_sat": len(models), "solver_unsat": 127,
          "sat_models": models, "sage_chart_sha256": sha(PARENT / "audit_result.json"),
          "journal_sha256": sha(HERE / "slice_results.jsonl"),
          "protocol_sha256": sha(HERE / "slice_protocol.json")}
with (HERE / "slice_model_audit.json").open("x") as stream:
    json.dump(output, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(output["status"], len(models))
