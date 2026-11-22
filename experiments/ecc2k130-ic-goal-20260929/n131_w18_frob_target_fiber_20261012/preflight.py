"""Compare batched target-Frobenius residuals with independent scalar group operations."""

import json
import time
from pathlib import Path

import frob

HERE = Path(__file__).resolve().parent


def main():
    target = frob.terminal.base.target_record()
    raw = target["preimages"][0]["point"]
    states = frob.terminal.pool()["states"]
    t0 = time.monotonic_ns()
    fast = frob.residuals(raw)
    t1 = time.monotonic_ns()
    naive = []
    for rotation, rotated_target in enumerate(frob.orbit(raw)):
        for state_index, state in enumerate(states):
            point = frob.terminal.prepare.subtract(rotated_target,
                                                   state["rotated_raw_point"])
            assert point is not None and point[0] not in (0, 1)
            reciprocal = frob.terminal.independent.inverse(point[0])
            naive.append({"target_rotation": rotation,
                          "terminal_state_index": state_index,
                          "point": list(point), "standard_reciprocal": reciprocal})
    t2 = time.monotonic_ns()
    assert fast == naive and len(fast) == 524
    exceptional = sum(rotated_target[0] == state["rotated_raw_point"][0]
                      for rotated_target in frob.orbit(raw) for state in states)
    parent = json.loads((frob.PARENT / "query_result.json").read_text())
    for index in range(4):
        assert fast[index]["point"] == parent["residuals"][index]["point"]
        assert fast[index]["standard_reciprocal"] == parent["residuals"][index]["standard_reciprocal"]
    result = {"status": "PASS_EXACT_524_BATCH_RESIDUAL_REPLAY",
              "curve_id": "EC1N131Ckb1heb5f1998f20b",
              "workload_id": target["workload_id"],
              "public_target": target["public_target"],
              "raw_preimage_index": 0,
              "target_rotations": 131,
              "terminal_states_per_rotation": 4,
              "residuals": len(fast),
              "distinct_reciprocals": len({row["standard_reciprocal"] for row in fast}),
              "exceptional_denominators": exceptional,
              "fast_ns_exploratory": t1-t0,
              "naive_ns_exploratory": t2-t1,
              "sha256": {"script": frob.sha(Path(__file__)),
                         "runner": frob.sha(HERE / "frob.py"),
                         "parent_query": frob.sha(frob.PARENT / "query_result.json"),
                         "parent_pool": frob.sha(frob.PARENT / "pool.json"),
                         "independent_field_group": frob.sha(frob.terminal.VERIFY / "verify.py")}}
    frob.save("preflight_result.json", result)
    print(json.dumps({"status": result["status"], "fast_seconds": (t1-t0)/1e9,
                      "naive_seconds": (t2-t1)/1e9}), flush=True)


if __name__ == "__main__":
    main()
