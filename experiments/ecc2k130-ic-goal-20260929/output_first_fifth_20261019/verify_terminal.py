"""Check the frozen output-first experiment and independent Sage receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
protocol = json.loads((HERE / "terminal_protocol.json").read_text())
assert protocol["status"] == "FROZEN_BEFORE_OUTPUT_FIRST_TERMINAL_AUDIT"
assert protocol["candidate_id"] is None
for label, source in protocol["sources"].items():
    assert sha(source["path"]) == source["sha256"], label

summary = {}
for case, expected_code, expected_prefix, expected_first, expected_curve, rank in (
    ("n41", 63, [0, 1, 1, 1], [96, 783, 555, 253],
     "EC1N41Ckb1h7d5e80d3c4d0", 10),
    ("n131", 29, [1, 1, 0, 1], [3, 18, 19, 22],
     "EC1N131Ckb1heb5f1998f20b", 32),
):
    producer = json.loads((HERE / f"{case}_result.json").read_text())
    audit = json.loads((HERE / f"{case}_audit_result.json").read_text())
    receipt = json.loads((HERE / f"{case}_audit_receipt.json").read_text())
    producer_protocol = json.loads((HERE / f"{case}_protocol.json").read_text())
    audit_protocol = json.loads((HERE / f"{case}_audit_protocol.json").read_text())
    for name, subprotocol in (("producer", producer_protocol),
                              ("audit", audit_protocol)):
        for label, source in subprotocol["sources"].items():
            assert sha(source["path"]) == source["sha256"], (case, name, label)
    assert producer["status"] == "COMPLETE_OUTPUT_FIRST_FIFTH"
    assert producer["candidate_id"] is None
    assert producer["curve_id"] == expected_curve
    assert producer["protocol_sha256"] == sha(HERE / f"{case}_protocol.json")
    assert producer["script_sha256"] == sha(HERE / "run.py")
    assert producer["math_sha256"] == sha(HERE / "output_first_math.py")
    assert producer["source_product_rank"] == rank
    assert producer["boxes_completed"] == 9
    assert producer["public_relations"] == 0
    assert producer["wall_seconds"] < producer_protocol["wall_cap_seconds"]
    assert producer["peak_rss_raw"] < producer_protocol["rss_cap_bytes"]
    assert all(row["prefix_assignments"] == 256 for row in producer["rows"])
    assert sum(row["status_counts"].get("OUTSIDE_PRODUCT_SUBSPACE", 0)
               for row in producer["rows"]) == 2303
    assert all(not row["verified_relations"] for row in producer["rows"][1:])
    positive = producer["rows"][0]["verified_relations"]
    assert len(positive) == 1
    assert positive[0]["prefix_choice_indices"] == expected_prefix
    assert positive[0]["first_four_codes"] == expected_first
    assert positive[0]["last_code"] == expected_code
    assert len(set(positive[0]["factor_columns"])) == 10
    assert audit["status"] == "PASS_INDEPENDENT_OUTPUT_FIRST_SAGE_AUDIT"
    assert audit["candidate_id"] is None
    assert audit["protocol_sha256"] == sha(HERE / f"{case}_audit_protocol.json")
    assert audit["script_sha256"] == sha(HERE / "audit_sage.py")
    assert audit["residuals_checked"] == 2304
    assert audit["source_product_rank"] == rank
    assert audit["verified_relations"] == 1
    assert audit["rows"][0]["verified_relations"][0]["last_code"] == expected_code
    assert [row["status_counts"] for row in producer["rows"]] == [
        row["status_counts"] for row in audit["rows"]]
    assert receipt["status"] == "COMPLETE" and receipt["exit_code"] == 0
    assert receipt["stop_reason"] is None and receipt["monitor_error"] is None
    assert receipt["command"][:2] == ["/Volumes/SSD990/cryptanalysis/sage", "-python"]
    assert receipt["protocol_sha256"] == sha(HERE / f"{case}_audit_protocol.json")
    assert receipt["result_sha256"] == sha(HERE / f"{case}_audit_result.json")
    assert receipt["stdout_sha256"] == sha(HERE / f"{case}_audit.stdout")
    assert receipt["stderr_sha256"] == sha(HERE / f"{case}_audit.stderr")
    assert (HERE / f"{case}_audit.stderr").read_bytes() == b""
    assert receipt["wall_seconds"] < audit_protocol["wall_cap_seconds"]
    assert receipt["sampled_peak_combined_rss_bytes"] < audit_protocol["rss_cap_bytes"]
    summary[case] = {"residuals_checked": 2304, "recovered_last_code": expected_code,
                     "public_relations": 0, "independent_sage_audit": True,
                     "producer_wall_seconds": producer["wall_seconds"],
                     "audit_wall_seconds": receipt["wall_seconds"]}

n41_gate = json.loads((HERE / "n41_gate.json").read_text())
assert n41_gate["status"] == "PASS_UNPINNED_N41_OUTPUT_FIRST_GATE"
assert n41_gate["recovered_last_code"] == 63
lean_output = (HERE / "lean_check.stdout").read_text()
for theorem in ("source_product_additive", "unique_source_code",
                "recover_product", "pair_law_product", "product_from_output"):
    assert f"'OutputFirst.{theorem}'" in lean_output
assert "sorryAx" not in lean_output
assert (HERE / "lean_check.stderr").read_bytes() == b""

result = {"status": "PASS_OUTPUT_FIRST_FIFTH_FINITE_PANEL_AUDIT",
          "candidate_id": None, "cases": summary,
          "protocol_sha256": sha(HERE / "terminal_protocol.json"),
          "verifier_sha256": sha(Path(__file__))}
(HERE / "terminal_result.json").write_text(json.dumps(result, sort_keys=True,
                                                    indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
