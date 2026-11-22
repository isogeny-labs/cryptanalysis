"""Independent read-only audit of source bindings and recorded gate counts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    baseline = json.loads((ROOT / "n131_w20_quadratic_two_pair_inverse_20261016"
                           / "full_result_v2.json").read_text())
    sample, full = read("sample_result.json"), read("full_result.json")
    native, receipt, protocol = read("native_result.json"), read("native_receipt.json"), \
        read("native_protocol.json")
    assert baseline["workload_id"] == sample["workload_id"] == full["workload_id"] \
        == protocol["workload_id"] == "cc09e7eb202a"
    assert sample["direct_partner_root_checks"] == 512
    assert sample["exceptional_cases"] == full["exceptional_cases"] == 0
    assert full["left_codes"] == 132045
    assert full["target_quadratic_calls"] == baseline["right_quadratic_queries"] // 2
    assert [r["proposals"] for r in full["preimage_rows"]] == \
        [r["proposals"] for r in baseline["preimage_rows"]] == [528180]*4
    assert full["eligible_source_hits"] == baseline["eligible_source_hits"] == []
    assert native["status"] == "COMPLETE_FUSED_PAIR_QUERY"
    assert native["valid_codes"] == 132045 and native["left_roots"] == 264090
    assert len(native["queries"]) == 4
    assert all(q["left"] == 264090 and q["full_span_hits"] == 0
               and q["valid_code_hits"] == 0 and q["distinct_column_hits"] == 0
               and q["exceptional_quadratics"] == 0 and not q["capped"] and not q["oom"]
               for q in native["queries"])
    assert native["roots_recovered"] == 0
    assert receipt["status"] == "EXIT_0" and receipt["exit_code"] == 0
    assert receipt["result_sha256"] == sha(HERE / "native_result.json")
    assert receipt["protocol_sha256"] == sha(HERE / "native_protocol.json")
    assert native["peak_rss_bytes"] < protocol["rss_cap_bytes"]
    assert native["setup_ns"] + native["query_ns"] < protocol["wall_cap_seconds"]*10**9
    source_paths = {
        "source": HERE / "native_pair.cpp", "helpers": HERE / "native_helpers.hpp",
        "binary": HERE / "native_pair", "charts": HERE / "public_charts.txt",
        "preimages": ROOT / "n131_fixed_seed_eight_pair_circuit_20261010/target_preimages.json",
        "support": ROOT / "n131_w20_sevenpair_gate_20261010/support_w20.tsv",
        "valid": ROOT / "n131_w20_code_trace_bitset_20261014/valid_bitmap.bin",
        "runtime": HERE / "sage_runtime_info.json", "runner": HERE / "native_run.py"}
    assert protocol["sources"] == {key: sha(path) for key, path in source_paths.items()}
    axioms = (HERE / "lean_output.txt").read_text().splitlines()
    assert len(axioms) == 4 and all("[propext, Classical.choice, Quot.sound]" in row
                                    for row in axioms)
    result = {"status": "PASS_FROZEN_TORSION_PAIRED_GATE",
              "workload_id": protocol["workload_id"],
              "sample_root_checks": sample["direct_partner_root_checks"],
              "sage_quadratic_calls": full["target_quadratic_calls"],
              "native_full_preimage_span_hits": [q["full_span_hits"] for q in native["queries"]],
              "native_query_ns": native["query_ns"],
              "source_hashes_checked": len(source_paths),
              "lean_declarations_audited": len(axioms)}
    with (HERE / "verification.json").open("x") as out:
        json.dump(result, out, indent=2, sort_keys=True)
        out.write("\n")
    print(result["status"])


if __name__ == "__main__":
    main()
