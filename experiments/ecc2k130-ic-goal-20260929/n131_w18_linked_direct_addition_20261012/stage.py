"""Measure the direct linked-addition gate on the frozen constructed target."""

import hashlib
import json
import resource
import time
from pathlib import Path

import direct

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / "stage_protocol.json").read_text())
assert protocol["status"] == "FROZEN_BEFORE_DIRECT_ADDITION_STAGE_BUILD"
for key, filename in {
    "stage": "stage.py",
    "gate": "direct.py",
    "fixture": "control_fixture.json",
    "candidate_protocol": "protocol.json",
}.items():
    assert protocol["sha256"][key] == sha(HERE / filename), key
chain = json.loads((HERE / "control_fixture.json").read_text())
rows = direct.prior.orbit9.orbit_rows(
    direct.prior.orbit9.constructed_preimages(chain["raw_target"]))
_, root, nodes = direct.base.source_domain()
start = time.monotonic_ns()
circuit, wires = direct.build([row["standard_reciprocal"] for row in rows],
                               root, nodes)
elapsed = time.monotonic_ns() - start
assert len(wires["linked_x_inverse"]) == 131
result = {
    "status": "PASS_N131_LINKED_DIRECT_ADDITION_CONSTRUCTED_CIRCUIT_BUILD",
    "candidate_id": None,
    "field_degree": 131,
    "public_target": chain["public_target"],
    "formula_variables": circuit.next_var - 1,
    "formula_and_gates": circuit.and_count,
    "formula_clauses": len(circuit.clauses),
    "formula_native_xor_rows": len(circuit.xors),
    "build_wall_ns_exploratory": elapsed,
    "parent_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    "stage_protocol_sha256": sha(HERE / "stage_protocol.json"),
}
with (HERE / "stage_result.json").open("x") as stream:
    json.dump(result, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(result["status"], result["formula_variables"],
      result["formula_clauses"], elapsed / 1e9, flush=True)
