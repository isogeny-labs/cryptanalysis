"""Replay the first d13/m12 preparation target without starting SAT."""

import hashlib
import json
import random
import time
from pathlib import Path

import run_d13_m12_single_target as run


HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    manifest = json.loads(run.MANIFEST.read_text())
    protocol = json.loads(run.PROTOCOL.read_text())
    workload = json.loads(run.WORKLOAD.read_text())
    curve_data = json.loads(run.CURVE_RECORD.read_text())
    formula_receipt_path = run.PROBE / "d13_m12_formula_and_planted_control_v1.json"
    frozen = json.loads(formula_receipt_path.read_text())["formula_counts"]
    frozen_stats = {"vars": frozen["variables"],
                    "clauses": frozen["clauses"], "xors": frozen["native_xors"]}
    assert frozen["records"] == frozen["clauses"] + frozen["native_xors"]

    start = time.perf_counter_ns()
    context, public_target, _, _ = run.common.build_context(
        curve_data, workload, manifest)
    setup_ns = time.perf_counter_ns() - start
    onb, curve, order, _, generator, basis_masks, _, _, _, valid_codes, \
        official_q, fiber_coordinates = context
    scalar = random.Random(protocol["run_control"]["precomputation_seed"]).randrange(1, order)
    preparation_target = curve.mul(generator, scalar)
    rows = {}
    for name, target in (("official_public_q", public_target),
                         ("first_preparation_target", preparation_target)):
        start = time.perf_counter_ns()
        formula, _, roots, _, phi_masks = run.pipeline.target_relation_formula(
            onb, curve, order, target, basis_masks, valid_codes,
            official_q, fiber_coordinates)
        counts = formula.stats()
        rows[name] = {
            "formula_counts": counts,
            "root_count": len(roots),
            "endpoint_count": len(phi_masks),
            "counts_equal_frozen_public_q": counts == frozen_stats,
            "structural_root_count_passed": len(roots) == (run.pipeline.LEAVES - 1) * run.pipeline.N,
            "formula_has_records": counts["clauses"] + counts["xors"] > 0,
            "formula_build_wall_ns": time.perf_counter_ns() - start,
        }
    assert rows["official_public_q"]["counts_equal_frozen_public_q"]
    assert all(row["structural_root_count_passed"] and
               row["formula_has_records"] and row["endpoint_count"] == 4
               for row in rows.values())
    output = {
        "kind": "d13_m12_target_formula_count_diagnosis_v1",
        "status": "PASS_BOTH_FORMULAS_STRUCTURALLY_VALID",
        "candidate_id": protocol["candidate_id"],
        "first_preparation_scalar_sha256": hashlib.sha256(str(scalar).encode()).hexdigest(),
        "frozen_public_q_formula_counts": frozen,
        "factor_base_setup_wall_ns_exploratory": setup_ns,
        "rows": rows,
        "source_sha256": {"diagnostic": sha(__file__), "runner": sha(run.__file__),
                          "protocol": sha(run.PROTOCOL), "formula_receipt": sha(formula_receipt_path)},
    }
    with (HERE / "formula_count_diagnosis_20261115.json").open("x") as stream:
        json.dump(output, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(output["status"], rows["first_preparation_target"]["formula_counts"])


if __name__ == "__main__":
    main()
