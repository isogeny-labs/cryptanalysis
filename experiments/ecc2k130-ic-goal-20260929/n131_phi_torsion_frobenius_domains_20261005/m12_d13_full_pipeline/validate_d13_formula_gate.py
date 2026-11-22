"""Replay audited formula counts through the corrected d13/m12 gate."""

import hashlib
import json
from pathlib import Path

import run_d13_m12_single_target as run


HERE = Path(__file__).resolve().parent
DIAGNOSIS = HERE / "formula_count_diagnosis_20261115.json"
OUTPUT = HERE / "formula_gate_validation_v2_20261115.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    diagnosis = json.loads(DIAGNOSIS.read_text())
    expected = diagnosis["frozen_public_q_formula_counts"]
    assert run.common.validate_target_formula_counts is run.validate_d13_target_formula_counts
    checked = {}
    for name, row in diagnosis["rows"].items():
        stats = row["formula_counts"]
        roots = [None] * row["root_count"]
        endpoints = [None] * row["endpoint_count"]
        assert run.validate_d13_target_formula_counts(stats, roots, endpoints, expected)
        assert not run.validate_d13_target_formula_counts(
            {**stats, "xors": stats["xors"] + 1}, roots, endpoints, expected)
        assert not run.validate_d13_target_formula_counts(stats, roots[:-1], endpoints, expected)
        assert not run.validate_d13_target_formula_counts(stats, roots, endpoints[:-1], expected)
        assert not run.validate_d13_target_formula_counts(
            stats, roots, endpoints, {**expected, "records": expected["records"] + 1})
        checked[name] = {"positive_passed": True, "four_mutations_rejected": True,
                         "counts": stats, "roots": len(roots), "endpoints": len(endpoints)}
    receipt = {"kind": "d13_m12_formula_count_gate_validation_v1",
               "status": "PASS_EXACT_COUNTS_AND_STRUCTURAL_MUTATIONS",
               "candidate_id_before_refreeze": diagnosis["candidate_id"],
               "checked": checked,
               "source_sha256": {"validator": sha(__file__),
                                 "runner": sha(run.__file__),
                                 "diagnosis": sha(DIAGNOSIS)}}
    with OUTPUT.open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(receipt["status"], len(checked))


if __name__ == "__main__":
    main()
