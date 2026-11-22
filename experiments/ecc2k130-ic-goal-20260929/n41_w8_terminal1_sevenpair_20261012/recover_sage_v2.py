#!/usr/bin/env sage -python
"""Recover the N41 public scalar from a first-edge terminal relation."""

import hashlib
import json
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LOGS = ROOT / "n41_w8_sixpair_logprep_20261011/audit_result.json"
R = 549756390943


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    recovery_protocol = json.loads((HERE / "recovery_protocol_v2.json").read_text())
    assert recovery_protocol["status"] == "FROZEN_N41_TERMINAL4_RECOVERY"
    inputs = {"source": Path(__file__),
              "relations": HERE / "sage_audit_result_v2.json",
              "prepared_factor_logs": LOGS,
              "runtime": HERE / "sage_runtime_info.json"}
    assert recovery_protocol["sha256"] == {name: sha(path) for name, path in inputs.items()}
    audit = json.loads((HERE / "sage_audit_result_v2.json").read_text())
    prepared = json.loads(LOGS.read_text())
    runtime = json.loads((HERE / "sage_runtime_info.json").read_text())
    assert runtime["status"] == "verified"
    assert audit["status"] == "PASS_INDEPENDENT_N41_TERMINAL4_RELATION"
    assert prepared["status"] == "PASS_N41_FULL_FACTOR_LOG_AND_TARGET_RECOVERY"
    assert prepared["final_rank_including_generator_anchor"] == 70
    assert prepared["factor_base_folded_columns"] == 70
    assert len(prepared["factor_logs"]) == 70
    assert prepared["recovered_public_target"]["independent_scalar_replay"]
    assert audit["public_target_transported"] == prepared["recovered_public_target"]["public_target_transported"]
    assert audit["frobenius_eigenvalue_mod_r"] == prepared["frobenius_eigenvalue_mod_r"]
    target_log = int(prepared["recovered_public_target"]["target_log_mod_r"])
    start = time.monotonic_ns()
    recovered = []
    for row in audit["replayed"]:
        scalar = sum(int(term["coefficient_mod_r"]) *
                     int(prepared["factor_logs"][str(term["column"])])
                     for term in row["relation_row"]) % R
        assert scalar == target_log
        recovered.append(scalar)
    combined = time.monotonic_ns()
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, name="t", modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def dec(value):
        return field(ring([(int(value) >> i) & 1 for i in range(41)]))

    generator = curve(*map(dec, prepared["generator_projected"]))
    public = curve(*map(dec, audit["public_target_transported"]))
    assert R * generator == curve(0) and target_log * generator == public
    replayed = time.monotonic_ns()
    result = {"status": "PASS_TERMINAL4_N41_TARGET_SCALAR_RECOVERY",
              "candidate_id": None,
              "curve_id": audit["curve_id"],
              "verified_relation_count": len(recovered),
              "rank_from_empty_matrix": audit["rank_from_empty_matrix"],
              "factor_log_count": len(prepared["factor_logs"]),
              "factor_log_matrix_rank": prepared["final_rank_including_generator_anchor"],
              "recovered_scalar_mod_r": str(target_log),
              "all_relation_scalars_equal": len(set(recovered)) == 1,
              "independent_scalar_replay": True,
              "log_combination_ns_exploratory": combined-start,
              "curve_replay_ns_exploratory": replayed-combined,
              "source_sha256": {"script": sha(Path(__file__)),
                                "relations": sha(HERE / "sage_audit_result_v2.json"),
                                "prepared_factor_logs": sha(LOGS),
                                "sage_runtime": sha(HERE / "sage_runtime_info.json")},
              "recovery_protocol_sha256": sha(HERE / "recovery_protocol_v2.json")}
    with (HERE / "recovery_result_v2.json").open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(result["status"], result["recovered_scalar_mod_r"])


if __name__ == "__main__":
    main()
