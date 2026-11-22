"""Bind transitive archived arithmetic sources after the frozen solver runs."""
import hashlib
import json
from pathlib import Path


D = Path(__file__).resolve().parent
ROOT = D.parent
EXPERIMENTS = ROOT.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


in_goal = [
    "n41_sixpair_shared_target_20261017/circuit.py",
    "n131_w20_selector_elimination_v2_20261013/selector.py",
    "n131_w20_output_inverse_linear_20261012/linear.py",
    "n131_w20_inverse_trace_20261012/run.py",
    "n131_w20_sevenpair_gate_20261010/sevenpair_circuit.py",
    "n131_fixed_seed_ninepair_cubic_20261011/run.py",
    "n131_fixed_seed_eight_pair_circuit_20261010/fixed_pair_circuit.py",
    "n41_basis_aware_quartic_20261011/replay.py",
    "n41_basis_aware_quartic_20261011/sparse.py",
]
outside = ["koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py"]
record = {"schema": 1,
          "scope": "postrun source readback with byte-identical public XCNF rebuild",
          "goal_sources": {name: sha(ROOT / name) for name in in_goal},
          "experiment_sources": {name: sha(EXPERIMENTS / name) for name in outside},
          "local_sources": {name: sha(D / name) for name in (
              "circuit.py", "build.py", "freeze.py", "run_public.py", "run_public_v2.py")},
          "public_formula_sha256": sha(D / "public.xcnf"),
          "build_result_sha256": sha(D / "build_result.json"),
          "query_protocol_v2_sha256": sha(D / "query_protocol_v2.json"),
          "query_v2_result_sha256": sha(D / "query_v2_result.json"),
          "producer_sha256": sha(Path(__file__))}
(D / "dependency_manifest.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
print(sha(D / "dependency_manifest.json"))
