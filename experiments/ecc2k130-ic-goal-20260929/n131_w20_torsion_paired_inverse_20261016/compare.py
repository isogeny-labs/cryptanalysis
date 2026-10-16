"""Compare frozen fused/unfused receipts and the partner-side positive gate."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_run(prefix, result, receipt, protocol):
    assert receipt["status"] == "EXIT_0" and receipt["exit_code"] == 0
    assert receipt["result_sha256"] == sha(HERE / (prefix + "_result.json"))
    assert receipt["protocol_sha256"] == sha(protocol)
    assert result["left_roots"] == 264090 and result["valid_codes"] == 132045
    assert len(result["queries"]) == 4
    assert all(q["left"] == 264090 and q["gate_hits"] == 0
               and q["full_span_hits"] == 0 and q["valid_code_hits"] == 0
               and q["distinct_column_hits"] == 0 and q["exceptional_quadratics"] == 0
               and not q["capped"] and not q["oom"] for q in result["queries"])


def main():
    fused = read(HERE / "native_result.json")
    unfused = read(HERE / "unfused_result.json")
    repeat = read(HERE / "native_repeat_result.json")
    fused_receipt = read(HERE / "native_receipt.json")
    unfused_receipt = read(HERE / "unfused_receipt.json")
    repeat_receipt = read(HERE / "native_repeat_receipt.json")
    native_protocol = HERE / "native_protocol.json"
    unfused_protocol = HERE / "unfused_protocol.json"
    validate_run("native", fused, fused_receipt, native_protocol)
    validate_run("unfused", unfused, unfused_receipt, unfused_protocol)
    validate_run("native_repeat", repeat, repeat_receipt, native_protocol)
    assert fused["status"] == repeat["status"] == "COMPLETE_FUSED_PAIR_QUERY"
    assert unfused["status"] == "COMPLETE_UNFUSED_FOUR_QUERY"
    for name, protocol in (("unfused", unfused_protocol), ("native", native_protocol)):
        p = read(protocol)
        assert p["workload_id"] == "cc09e7eb202a"
        assert p["sources"]["charts"] == sha(HERE / "public_charts.txt")
        assert p["sources"]["support"] == sha(
            ROOT / "n131_w20_sevenpair_gate_20261010/support_w20.tsv")
        assert p["sources"]["valid"] == sha(
            ROOT / "n131_w20_code_trace_bitset_20261014/valid_bitmap.bin")
    positive = read(HERE / "positive_partner_partial.json")
    archived = read(ROOT / "n131_w20_quadratic_algebra_20261014/result_positive.json")
    assert positive["status"] == "CENSORED_TIME"
    assert positive["queries"][1]["hits"] == archived["query"]["hits"]
    assert positive["queries"][1]["distinct_column_hits"] == 1
    assert positive["queries"][1]["left"] > 0
    assert positive["queries"][1]["left"] < 264090
    timings = [fused["query_ns"], repeat["query_ns"]]
    result = {"status": "PASS_FUSED_UNFUSED_RECEIPTS",
              "curve_id": "EC1N131Ckb1heb5f1998f20b",
              "workload_id": "cc09e7eb202a", "candidate_id": None,
              "fused_query_ns": timings,
              "unfused_query_ns": unfused["query_ns"],
              "exploratory_unfused_over_first_fused": unfused["query_ns"]/timings[0],
              "exploratory_unfused_over_second_fused": unfused["query_ns"]/timings[1],
              "positive_partner_side_hit": positive["queries"][1]["hits"][0],
              "positive_control_status": positive["status"]}
    with (HERE / "comparison.json").open("x") as out:
        json.dump(result, out, indent=2, sort_keys=True)
        out.write("\n")
    print(result["status"])


if __name__ == "__main__":
    main()
