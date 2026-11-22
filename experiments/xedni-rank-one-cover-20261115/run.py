"""Evaluate the checked rank-one cover gate on the pinned eight-field panel."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
INPUT = PARENT / "xedni-large-order-admission-20261115" / "result.json"
CONTROL = PARENT / "xedni-rank-one-coordinate-control-20261115" / "result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert sha(INPUT) == protocol["selected_fields_result_sha256"]
    assert sha(CONTROL) == protocol["rank_one_control_result_sha256"]
    chosen = [r for r in json.loads(INPUT.read_text())["rows"] if r["selected"]]
    control = {r["field_prime"]: r for r in json.loads(CONTROL.read_text())["rows"]}
    assert len(chosen) == len(control) == 8
    par = protocol["parameters"]
    L, c, K, T = (par[k] for k in ("L", "c", "K", "T"))
    box = (4 * L + 1) ** par["lift_arity"] - 1
    capacity = T * (2 * K + 1)
    rows = []
    for item in chosen:
        p, q = item["field_prime"], item["subgroup_order"]
        measured = control[p]
        assert measured["subgroup_order"] == q
        assert K <= c * L and T * (2 * c + 1) < L and box < q
        assert capacity < q
        measured_K = measured["two_point_sum_coordinate_radius_K"]
        rows.append({"field_prime": p, "subgroup_order": q,
                     "witness_box": box, "rank_gap_left": T * (2 * c + 1),
                     "allowed_coordinate_radius": K, "cover_capacity": capacity,
                     "uncovered_residues_at_least": q - capacity,
                     "measured_centered_sum_radius": measured_K,
                     "measured_exceeds_allowed": measured_K > K})
    print(json.dumps({"schema": "xedni-rank-one-cover-result-v1", "status": "PASS",
                      "protocol_sha256": sha(HERE / "protocol.json"),
                      "source_sha256": sha(Path(__file__)),
                      "input_sha256": sha(INPUT), "control_sha256": sha(CONTROL),
                      "parameters": par, "rows": rows}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
