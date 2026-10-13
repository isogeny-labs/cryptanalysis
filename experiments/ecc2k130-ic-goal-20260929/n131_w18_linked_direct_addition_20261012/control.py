"""Bind the one additional inverse witness in the inherited full control."""

import hashlib
import json
from pathlib import Path

import direct

HERE = Path(__file__).resolve().parent
prior = direct.prior
base = direct.base


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / "control_protocol.json").read_text())
assert protocol["status"] == "FROZEN_BEFORE_DIRECT_ADDITION_CONSTRUCTED_CONTROL"
for key, filename in {
    "control": "control.py",
    "gate": "direct.py",
    "candidate_protocol": "protocol.json",
    "stage_result": "stage_result.json",
    "fixture": "control_fixture.json",
}.items():
    assert protocol["sha256"][key] == sha(HERE / filename), key

old_build = prior.build
old_complete = base.complete_assignment
captured = {}


def build(*args):
    circuit, wires = old_build(*args)
    captured["wires"] = wires
    return circuit, wires


def complete(circuit, assignment):
    wires = captured["wires"]
    a = sum((assignment[wire] << bit)
            for bit, wire in enumerate(wires["outputs"][0]))
    x = base.inverse(a)
    assert direct.pair.gf_mul(a, x) == 1
    for bit, wire in enumerate(wires["linked_x_inverse"]):
        assert wire not in assignment
        assignment[wire] = (x >> bit) & 1
    captured["pair_reciprocal"] = a
    captured["inverse_x"] = x
    return old_complete(circuit, assignment)


prior.build = build
base.complete_assignment = complete
try:
    prior.control()
finally:
    prior.build = old_build
    base.complete_assignment = old_complete

result = json.loads((HERE / "control_result.json").read_text())
assert result["status"] == "PASS_FULL_N131_LINKED_TENPAIR_CONSTRUCTED_WITNESS"
with (HERE / "direct_control_result.json").open("x") as stream:
    json.dump({
        "status": "PASS_FULL_N131_DIRECT_LINKED_ADDITION_CONSTRUCTED_ASSIGNMENT",
        "candidate_id": None,
        "pair_reciprocal": captured["pair_reciprocal"],
        "linked_x_inverse": captured["inverse_x"],
        "inherited_control_sha256": sha(HERE / "control_result.json"),
        "formula_sha256": result["formula"]["xcnf_sha256"],
        "control_protocol_sha256": sha(HERE / "control_protocol.json"),
    }, stream, indent=2, sort_keys=True)
    stream.write("\n")
print("PASS_FULL_N131_DIRECT_LINKED_ADDITION_CONSTRUCTED_ASSIGNMENT", flush=True)
