"""Recover and independently classify the v2 SAT control after decoder failure."""

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


frozen = json.loads((HERE / "recover_protocol.json").read_text())
assert frozen["status"] == "FROZEN_BEFORE_N41_V2_CONTROL_RECOVERY"
for key, path in {
    "source": Path(__file__), "runner": HERE / "run.py",
    "protocol": HERE / "protocol.json", "formula": HERE / "control.xcnf",
    "stdout": HERE / "control.stdout", "stderr": HERE / "control.stderr",
    "build": HERE / "control.build.json",
}.items():
    assert frozen["sha256"][key] == sha(path), key

spec = importlib.util.spec_from_file_location("v2_recovery_runner", HERE / "run.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
lists, targets = runner.old.source()
witness = runner.linked_witness(lists, targets)
circuit, wires = runner.formula(lists, targets, True, witness)
profile = json.loads((HERE / "control.build.json").read_text())
assert circuit.next_var - 1 == profile["variables"]
assert len(circuit.clauses) == profile["cnf_clauses"]
assert len(circuit.xors) == profile["native_xor_rows"]
assert profile["sha256"] == sha(HERE / "control.xcnf")

parser_path = GOAL / "n41_n131_fouratom_product_anf_sat_20261012/run.py"
spec = importlib.util.spec_from_file_location("v2_recovery_parser", parser_path)
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)
stdout = (HERE / "control.stdout").read_text()
assert "s SATISFIABLE" in stdout
model = parser.model(stdout, circuit.next_var - 1)
checked = parser.check_formula(HERE / "control.xcnf", model)
assert checked == {"cnf_clauses_checked": len(circuit.clauses),
                   "native_xor_rows_checked": len(circuit.xors)}


def bit(wire):
    return (0 if wire == 0 else 1 if wire == -1 else
            model[wire] if wire > 0 else 1 - model[-wire])


ids = [[index for index, wire in enumerate(row) if bit(wire)]
       for row in wires["selectors"]]
flags = [index for index, wire in enumerate(wires["flags"]) if bit(wire)]
assert all(len(row) == 1 for row in ids) and len(flags) == 1
ids = [row[0] for row in ids]
assert ids[0] == ids[1]
edges = [lists[slot][sid]["edge"] for slot, sid in zip(runner.old.SLOTS, ids)]
assert edges[0] == edges[1] and len(set(edges)) == 9
nodes = [lists[slot][sid]["point"] for slot, sid in zip(runner.old.SLOTS, ids)]
for index, (left, right) in enumerate(runner.old.TREE):
    point = runner.old.add(nodes[left], nodes[right])
    assert point is not None and nodes[left][0] != nodes[right][0]
    xbits, ybits = wires["outputs"][index]
    observed = (sum(bit(wire) << j for j, wire in enumerate(xbits)),
                sum(bit(wire) << j for j, wire in enumerate(ybits)))
    assert point == observed
    nodes.append(point)
assert nodes[-1] == targets[flags[0]]
assert ids == witness["state_ids"] and flags[0] == witness["target_index"]
with (HERE / "recover_result.json").open("x") as stream:
    json.dump({"status": "PASS_N41_V2_SAT_CONTROL_RECOVERED_AFTER_DECODER_ERROR",
               "candidate_id": None, "selected_state_ids": ids,
               "raw_preimage_index": flags[0], "raw_sum": nodes[-1],
               "model_rows_checked": checked,
               "recover_protocol_sha256": sha(HERE / "recover_protocol.json")},
              stream, sort_keys=True, indent=2)
    stream.write("\n")
print("PASS_N41_V2_SAT_CONTROL_RECOVERED_AFTER_DECODER_ERROR", flush=True)
