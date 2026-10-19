"""Hash-bound terminal audit of N131 sign-norm transfer and direct baseline."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg = json.loads((HERE / "terminal_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_N131_SIGN_NORM_TERMINAL"
for label, source in cfg["sources"].items():
    assert sha(source["path"]) == source["sha256"], label
for name in ("panel_protocol.json", "run_protocol_positive.json",
             "run_protocol_public.json", "audit_protocol.json",
             "direct_protocol.json", "positive_gate_protocol.json"):
    protocol = json.loads((HERE / name).read_text())
    for label, source in protocol["sources"].items():
        assert sha(source["path"]) == source["sha256"], (name, label)
positive = json.loads((HERE / "positive_result.json").read_text())
ordinary = json.loads((HERE / "public_result.json").read_text())
audit = json.loads((HERE / "audit_result.json").read_text())
direct = json.loads((HERE / "direct_result.json").read_text())
assert positive["status"] == ordinary["status"] == "COMPLETE_N131_SIGN_NORM"
assert positive["rows"][0]["group_hits"] == [[0, 27]]
assert positive["rows"][0]["trace_mask"] is None
assert positive["rows"][0]["norm_rank"] == 31
assert ordinary["boxes_completed"] == ordinary["certified_public_boxes"] == 8
assert ordinary["public_group_hits"] == 0
for row in ordinary["rows"]:
    assert row["norm_rank"] == 32 and row["trace_mask"] is not None
    assert row["group_hits"] == []
    assert row["trace_anf"] == [1] + [0] * 31
    assert all((row["trace_mask"] & value).bit_count() % 2 == 1
               for value in row["norms"])
assert audit["status"] == "PASS_INDEPENDENT_N131_SIGN_NORM_AUDIT"
assert audit["source_codes_rebuilt"] == 55
assert audit["assignments_replayed"] == 9216
assert audit["norm_products_checked"] == 288
assert audit["trace_values_checked"] == 256
assert audit["public_boxes_rejected"] == 8
assert direct["status"] == "COMPLETE_N131_DIRECT_ENUM"
assert direct["boxes_completed"] == 8 and direct["assignments_checked"] == 8192
assert direct["group_hits"] == 0
for label in ("panel", "positive", "public", "audit", "direct"):
    receipt = json.loads((HERE / (label + "_receipt.json")).read_text())
    assert receipt["status"] == "COMPLETE" and receipt["exit_code"] == 0
    assert receipt["stop_reason"] is None and receipt["monitor_error"] is None
    assert receipt["command"][0] == "/Volumes/SSD990/cryptanalysis/sage"
    assert receipt["sampled_peak_combined_rss_bytes"] < 4294967296
    assert receipt["wall_seconds"] < (600 if label == "public" else 180)
    output_name = "panel.json" if label == "panel" else label + "_result.json"
    assert receipt["result_sha256"] == sha(HERE / output_name)
    assert receipt["stdout_sha256"] == sha(HERE / (label + ".stdout"))
    assert receipt["stderr_sha256"] == sha(HERE / (label + ".stderr"))
    assert (HERE / (label + ".stderr")).read_bytes() == b""
core_seconds = sum(row["coefficient_seconds"] + row["norm_seconds"]
                   for row in ordinary["rows"])
direct_seconds = direct["enumeration_seconds"]
assert core_seconds > direct_seconds > 0
result = {"status": "PASS_N131_SIGN_NORM_TRANSFER_AND_BASELINE_AUDIT",
          "candidate_id": None, "curve_id": cfg["curve_id"],
          "public_boxes_certified": 8, "finite_public_assignments": 8192,
          "independent_assignments_replayed": 9216,
          "sign_norm_core_seconds": core_seconds,
          "direct_enum_core_seconds": direct_seconds,
          "core_cost_ratio_sign_over_direct": core_seconds / direct_seconds,
          "protocol_sha256": sha(HERE / "terminal_protocol.json"),
          "verifier_sha256": sha(Path(__file__))}
(HERE / "terminal_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, sort_keys=True))
