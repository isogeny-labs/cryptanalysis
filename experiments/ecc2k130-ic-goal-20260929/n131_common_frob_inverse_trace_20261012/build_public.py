"""Build the unpinned N131 five-pair formula on four transformed raw fibers."""

import hashlib
import json
import time
from pathlib import Path

import circuit

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
TARGET = HERE / "target_result.json"
TARGET_PRIOR = GOAL / "n41_common_frob_factor_20261012/n131_projection_result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "query_protocol.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_N131_INVERSE_TRACE_PUBLIC_QUERY"
    assert protocol["sha256"]["builder"] == sha(HERE / "build_public.py")
    assert protocol["sha256"]["circuit"] == sha(HERE / "circuit.py")
    assert protocol["sha256"]["prior_target"] == sha(TARGET_PRIOR)
    target = json.loads(TARGET.read_text())
    assert target["status"] == "PASS_CHECKED_SAGE_N131_COMMON_FACTOR_TARGET"
    prior = json.loads(TARGET_PRIOR.read_text())
    for key in ("curve_id", "public_point", "transformed_target",
                "raw_preimages", "raw_preimage_reciprocals", "factor_mod_r"):
        assert target[key] == prior[key]
    assert target["raw_preimage_reciprocals"] == protocol["raw_preimage_reciprocals"]
    assert len(target["raw_preimages"]) == 4
    start = time.monotonic_ns()
    formula, wires, metadata = circuit.build(target["raw_preimage_reciprocals"])
    built = time.monotonic_ns()
    assert len(wires["target_flags"]) == 4
    output = HERE / "public.xcnf"
    assert not output.exists()
    formula.write(output)
    ended = time.monotonic_ns()
    result = {"status": "PUBLIC_FORMULA_BUILT", "candidate_id": None,
              "curve_id": target["curve_id"], "public_point": target["public_point"],
              "transformed_target": target["transformed_target"],
              "raw_preimages": target["raw_preimages"],
              "raw_preimage_reciprocals": target["raw_preimage_reciprocals"],
              "variables": formula.next_var-1, "and_gates": formula.and_count,
              "cnf_clauses": len(formula.clauses), "native_xor_rows": len(formula.xors),
              "xcnf_bytes": output.stat().st_size, "xcnf_sha256": sha(output),
              "target_flags": wires["target_flags"], "mask_wires": wires["masks"],
              "inverse_witness_wires": wires["inverse_witnesses"],
              "pair_output_wires": wires["pair_outputs"], "middle_wires": wires["middle"],
              "metadata": metadata, "construction_ns": built-start,
              "serialization_ns": ended-built,
              "protocol_sha256": sha(HERE / "query_protocol.json")}
    with (HERE / "public_build_result.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print("PUBLIC_FORMULA_BUILT", result["variables"], flush=True)


if __name__ == "__main__":
    main()
