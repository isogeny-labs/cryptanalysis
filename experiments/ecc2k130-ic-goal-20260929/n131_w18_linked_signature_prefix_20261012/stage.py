"""Build the signature-gated constructed circuit and record exact size."""

import hashlib
import json
import resource
import time
from pathlib import Path

import gate

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / "stage_protocol.json").read_text())
for key, filename in {
    "stage_source": "stage.py",
    "gate_source": "gate.py",
    "table": "rows.tsv.gz",
    "hash": "hash_manifest.json",
    "fixture": "control_fixture.json",
}.items():
    assert sha(HERE / filename) == protocol["sha256"][key], key
chain = json.loads((HERE / "control_fixture.json").read_text())
target_rows = gate.prior.orbit9.orbit_rows(
    gate.prior.orbit9.constructed_preimages(chain["raw_target"]))
_, root, nodes = gate.prior.base.source_domain()
start = time.monotonic_ns()
circuit, wires = gate.build([row["standard_reciprocal"] for row in target_rows],
                            root, nodes)
elapsed = time.monotonic_ns() - start
assert wires["intermediates"][0]
result = {
    "status": "PASS_LINKED_SIGNATURE_CONSTRUCTED_CIRCUIT_BUILD",
    "candidate_id": None,
    "field_degree": 131,
    "public_target": chain["public_target"],
    "formula_variables": circuit.next_var - 1,
    "formula_and_gates": circuit.and_count,
    "formula_clauses": len(circuit.clauses),
    "formula_native_xor_rows": len(circuit.xors),
    "signature_gate": circuit.signature_gate_stats,
    "build_wall_ns_exploratory": elapsed,
    "parent_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    "protocol_sha256": sha(HERE / "stage_protocol.json"),
}
with (HERE / "stage_result.json").open("x") as stream:
    json.dump(result, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(result["status"], result["formula_variables"],
      result["formula_clauses"], elapsed / 1e9)
