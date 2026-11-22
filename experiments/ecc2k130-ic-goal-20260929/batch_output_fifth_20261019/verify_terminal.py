"""Audit the frozen batch x-coordinate filter against direct and Sage paths."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
protocol = json.loads((HERE / "terminal_protocol.json").read_text())
assert protocol["status"] == "FROZEN_BEFORE_BATCH_OUTPUT_TERMINAL_AUDIT"
assert protocol["candidate_id"] is None
for label, source in protocol["sources"].items():
    assert sha(source["path"]) == source["sha256"], label

summary = {}
for case, expected_code, expected_prefix, curve_id in (
    ("n41", 63, [0, 1, 1, 1], "EC1N41Ckb1h7d5e80d3c4d0"),
    ("n131", 29, [1, 1, 0, 1], "EC1N131Ckb1heb5f1998f20b"),
):
    parity_protocol = json.loads((HERE / f"{case}_protocol.json").read_text())
    fast_protocol = json.loads((HERE / f"{case}_fast_protocol.json").read_text())
    for kind, subprotocol in (("parity", parity_protocol), ("fast", fast_protocol)):
        assert subprotocol["candidate_id"] is None
        assert subprotocol["worker_count"] == 1
        assert subprotocol["rss_cap_bytes"] == 4294967296
        assert subprotocol["wall_cap_seconds"] == (120 if case == "n41" else 600)
        for label, source in subprotocol["sources"].items():
            assert sha(source["path"]) == source["sha256"], (case, kind, label)
    parity = json.loads((HERE / f"{case}_result.json").read_text())
    fast = json.loads((HERE / f"{case}_fast_result.json").read_text())
    prior_dir = Path(parity_protocol["sources"]["prior_result"]["path"]).parent
    direct = json.loads((prior_dir / f"{case}_result.json").read_text())
    sage = json.loads((prior_dir / f"{case}_audit_result.json").read_text())
    assert parity["status"] == "PASS_BATCH_OUTPUT_PARITY"
    assert fast["status"] == "COMPLETE_BATCH_OUTPUT_FAST"
    assert parity["candidate_id"] is None and fast["candidate_id"] is None
    assert parity["curve_id"] == fast["curve_id"] == curve_id
    assert parity["protocol_sha256"] == sha(HERE / f"{case}_protocol.json")
    assert fast["protocol_sha256"] == sha(HERE / f"{case}_fast_protocol.json")
    assert parity["script_sha256"] == sha(HERE / "batch_output.py")
    assert fast["script_sha256"] == sha(HERE / "batch_output_fast.py")
    assert parity["boxes_completed"] == fast["boxes_completed"] == 9
    assert parity["residuals_checked"] == fast["residuals_checked"] == 2304
    assert fast["field_inverse_calls"] == 470
    assert parity["wall_seconds_including_direct_parity"] < parity_protocol["wall_cap_seconds"]
    assert fast["wall_seconds"] < fast_protocol["wall_cap_seconds"]
    assert max(parity["peak_rss_raw"], fast["peak_rss_raw"]) < 4294967296
    assert sage["status"] == "PASS_INDEPENDENT_OUTPUT_FIRST_SAGE_AUDIT"
    assert sage["residuals_checked"] == 2304 and sage["verified_relations"] == 1
    for j, (p, f, d, s) in enumerate(zip(parity["rows"], fast["rows"],
                                          direct["rows"], sage["rows"])):
        assert p["box_index"] == f["box_index"] == d["box_index"] == s["box_index"] == j
        assert p["status_counts"] == f["status_counts"] == d["status_counts"] == s["status_counts"]
        assert len(p["verified_relations"]) == len(f["verified_relations"]) == len(d["verified_relations"]) == len(s["verified_relations"]) == (1 if j == 0 else 0)
        if j == 0:
            for hit in (p["verified_relations"][0], f["verified_relations"][0],
                        d["verified_relations"][0], s["verified_relations"][0]):
                assert hit["last_code"] == expected_code
                assert hit["prefix_choice_indices"] == expected_prefix
                assert len(set(hit["factor_columns"])) == 10
    summary[case] = {"residuals_checked": 2304, "recovered_last_code": expected_code,
                     "field_inverse_calls": fast["field_inverse_calls"],
                     "batch_wall_seconds": fast["wall_seconds"],
                     "exact_direct_parity": True, "independent_sage_panel": True}

lean = (HERE / "lean_check.stdout").read_text()
for declaration in ("inverse_first_from_product", "inverse_last_from_product",
                    "nonzero_prod", "reverseBatch", "reverseBatch_correct"):
    assert f"'BatchOutput.{declaration}'" in lean
assert "sorryAx" not in lean
assert (HERE / "lean_check.stderr").read_bytes() == b""
result = {"status": "PASS_BATCH_OUTPUT_FIFTH_FINITE_PANEL_AUDIT",
          "candidate_id": None, "cases": summary,
          "protocol_sha256": sha(HERE / "terminal_protocol.json"),
          "verifier_sha256": sha(Path(__file__))}
(HERE / "terminal_result.json").write_text(json.dumps(result, sort_keys=True,
                                                    indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
