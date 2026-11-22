"""Verify original frozen runs after byte-for-byte relocation from /private/tmp."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL = Path("/private/tmp/ecc2k130-global-macaulay-20261019")
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()

def relocated(path):
    path = Path(path)
    if path.is_relative_to(ORIGINAL):
        return HERE / path.name
    return path

protocol = json.loads((HERE / "terminal_protocol.json").read_text())
assert protocol["status"] == "FROZEN_BEFORE_GLOBAL_MACAULAY_TERMINAL_AUDIT"
assert protocol["candidate_id"] is None
for label, source in protocol["sources"].items():
    assert sha(source["path"]) == source["sha256"], label

subprotocols = ["positive_protocol", "ordinary_protocol", "ordinary_rank7_protocol",
                "audit_protocol", "audit_v2_protocol", "dual_v3_protocol",
                "dual_verify_protocol"]
for name in subprotocols:
    p = json.loads((HERE / f"{name}.json").read_text())
    assert p["candidate_id"] is None, name
    for label, source in p["sources"].items():
        assert sha(relocated(source["path"])) == source["sha256"], (name, label)
    if name != "dual_verify_protocol":
        assert p["worker_count"] == 1
        assert p["wall_cap_seconds"] == 180
        assert p["rss_cap_bytes"] == 4294967296

positive = json.loads((HERE / "positive_result.json").read_text())
ordinary = json.loads((HERE / "ordinary_result.json").read_text())
for case, result in (("positive", positive), ("ordinary", ordinary)):
    assert result["status"] == "COMPLETE_GLOBAL_MACAULAY"
    assert result["candidate_id"] is None
    assert result["curve_id"] == "EC1N41Ckb1h7d5e80d3c4d0"
    assert result["protocol_sha256"] == sha(HERE / f"{case}_protocol.json")
    assert result["script_sha256"] == sha(HERE / "run.py")
    assert result["poly_monomials"] == 3046 and result["poly_max_degree"] == 4
    assert [(s["multiplier_degree"], s["rank"], s["reject"])
            for s in result["stages"]] == [(0, 41, False), (1, 861, False),
                                           (2, 8651, False)]
    assert result["wall_seconds"] < 180 and result["peak_rss_raw"] < 4294967296
    assert (HERE / f"{case}.stderr").read_bytes() == b""

rank7 = json.loads((HERE / "ordinary_rank7_result.json").read_text())
assert rank7["status"] == "COMPLETE_GLOBAL_MACAULAY"
assert rank7["candidate_id"] is None
assert rank7["poly_sha256"] == ordinary["poly_sha256"]
assert rank7["protocol_sha256"] == sha(HERE / "ordinary_rank7_protocol.json")
assert rank7["script_sha256"] == sha(HERE / "rank7.py")
assert rank7["wall_seconds"] < 180 and rank7["peak_rss_raw"] < 4294967296
assert [(s["multiplier_degree"], s["monomials"], s["rows_visited"],
         s["rank"], s["rank_only_unit_in_span"])
        for s in rank7["stages"]] == [(3, 137980, 55391, 55227, False)]
assert (HERE / "ordinary_rank7.stderr").read_bytes() == b""

first_audit_stderr = (HERE / "audit.stderr").read_text()
assert "TimeoutError: audit wall cap" in first_audit_stderr
assert (HERE / "audit.stdout").read_bytes() == b""
assert not (HERE / "audit_result.json").exists()
assert sha(HERE / "audit.stderr") == json.loads(
    (HERE / "audit_v2_protocol.json").read_text()
)["sources"]["attempt1_stderr"]["sha256"]

independent = json.loads((HERE / "audit_v2_result.json").read_text())
dual = json.loads((HERE / "dual_v3_result.json").read_text())
replay = json.loads((HERE / "dual_verify_result.json").read_text())
assert independent["status"] == "PASS_INDEPENDENT_GLOBAL_MACAULAY_RANK7_AUDIT"
assert dual["status"] == "PASS_GLOBAL_MACAULAY_DUAL_V3"
assert replay["status"] == "PASS_GLOBAL_MACAULAY_DUAL_REPLAY"
for name, result, script in (("audit_v2", independent, "audit_v2.py"),
                             ("dual_v3", dual, "dual_v3.py"),
                             ("dual_verify", replay, "verify_dual.py")):
    assert result["candidate_id"] is None
    assert result["protocol_sha256"] == sha(HERE / f"{name}_protocol.json")
    assert result["script_sha256"] == sha(HERE / script)
    assert (HERE / f"{name}.stderr").read_bytes() == b""
for result in (independent, dual):
    assert result["rows_checked"] == 55391
    assert result["rank"] == 55227 and result["augmented_unit_rank"] == 55228
    assert result["poly_sha256"] == ordinary["poly_sha256"]
    assert result["wall_seconds"] < 180 and result["peak_rss_raw"] < 4294967296
witness = int(dual["dual_witness_hex"], 16)
assert witness.bit_count() == dual["dual_witness_weight"] == 27832
assert witness & 1
assert replay["rows_checked"] == 55391
assert replay["unit_value"] == 1 and replay["row_values_all_zero"] is True
assert replay["dual_witness_weight"] == 27832
assert replay["poly_sha256"] == ordinary["poly_sha256"]

census = json.loads(Path(
    json.loads((HERE / "ordinary_protocol.json").read_text())["sources"]
    ["prior_census"]["path"]
).read_text())
assert census["status"] == "COMPLETE_N41_W11_ALLCODE_RESULTANT_CENSUS"
assert census["targets"][0]["zero_pairs"] == [[253, 63]]
assert census["targets"][1]["zero_pairs"] == []

lean = (HERE / "lean_check.stdout").read_text()
for theorem in ("annihilates_fold", "no_constant_certificate"):
    assert f"'GlobalMacaulayDual.{theorem}'" in lean
assert "sorryAx" not in lean
assert (HERE / "lean_check.stderr").read_bytes() == b""

result = {"status": "PASS_GLOBAL_TWO_FREE_DEGREE7_DUAL_AUDIT",
          "candidate_id": None, "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
          "ordinary_target_index": 1, "macaulay_degree": 7,
          "equation_degree": 4, "rows": 55391, "rank": 55227,
          "augmented_unit_rank": 55228, "dual_witness_weight": 27832,
          "independent_rows_checked": 55391,
          "first_audit_status": "WALL_CAP_PARTIAL_AUDIT",
          "protocol_sha256": sha(HERE / "terminal_protocol.json"),
          "verifier_sha256": sha(Path(__file__))}
(HERE / "terminal_result.json").write_text(json.dumps(result, sort_keys=True,
                                                    indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
