"""Freeze source and positive relation for the N41 selector control."""

import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parent
experiments = root.parent
paths = {"script": here / "n41_selector_control_sage.py",
         "selector": here / "binary_selector.py",
         "circuit": experiments / "koblitz-s5-invariant-20260924/circuit_sat.py",
         "input": root / "n41_w8_sixpair_mitm_20261011/protocol.json",
         "positive_relation": root / "n41_w8_ninepair_join_control_20261012/audit_result.json",
         "runtime": here / "sage_runtime_info.json"}
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

positive = json.loads(paths["positive_relation"].read_text())
assert positive["status"] == "PASS_INDEPENDENT_N41_PUBLIC_NINE_PAIR_RELATION"
record = {"status": "FROZEN_N41_BINARY_SELECTOR_CONTROL",
          "curve_id": positive["curve_id"],
          "public_target_transported": positive["public_target_transported"],
          "positive_raw_preimage_index": 0,
          "fiber_count": 4, "frobenius_rotations": 41,
          "selection_law": "two-bit fiber and six-bit Frobenius exponent 0..40",
          "source_sha256": {name: sha(path) for name, path in paths.items()}}
with (here / "n41_control_protocol.json").open("x") as stream:
    json.dump(record, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(record["status"])
