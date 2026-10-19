"""Hash-bound verification of the nonzero branch and W33 follow-up receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
protocol_path = HERE / "verification_protocol_v2.json"
protocol = json.loads(protocol_path.read_text())
assert protocol["status"] == "FROZEN_BEFORE_TERMINAL_VERIFICATION"
for label, source in protocol["sources"].items():
    assert sha(source["path"]) == source["sha256"], label


def read(name):
    return json.loads((HERE/name).read_text())


n41 = read("n41_gate.json")
positive = read("positive_gate.json")
positive_result = read("n131_p_k4_result.json")
positive_receipt = read("n131_p_k4_receipt.json")
public_result = read("n131_o_k4_result.json")
public_receipt = read("n131_o_k4_receipt.json")
gcd = read("w33_gcd_result.json")
direct = read("w33_direct_root_result.json")
assert n41["status"] == "PASS_N41_NONZERO_BRANCH_CONTROL"
assert positive["status"] == "PASS_N131_NONZERO_BRANCH_POSITIVE_GATE"
assert positive_result["status"] == "GB_COMPLETE"
assert positive_result["recovered_codes"] == {"first_code": 3, "second_code": 16722}
assert public_result["status"] == "GB_UNIT_IDEAL"
assert public_result["recovered_codes"] is None
assert positive_result["nonzero_branch_products_checked"] == 8
assert public_result["nonzero_branch_products_checked"] == 8
assert gcd["status"] == "COMPLETE_W33_GCD_AUDIT"
assert gcd["requested_rows"] == 32 and len(gcd["rows"]) == 32
assert [row["p_code"] for row in gcd["rows"] if row["target_index"] == 0 and not row["reject"]] == [3]
assert all(row["reject"] for row in gcd["rows"] if row["target_index"] == 1)
assert direct["status"] == "PASS_W33_DIRECT_ROOT_AND_CURVE_REPLAY"
assert [direct["first_code"], direct["second_code"]] == [3, 16722]
assert direct["matching_branch_pairs"]
assert direct["target_point"] == positive_result["target_point"]
assert all(x["candidate_id"] is None for x in
           (positive_result, public_result, gcd, direct))

for result, receipt, cap in ((positive_result, positive_receipt, 600),
                             (public_result, public_receipt, 600)):
    assert receipt["status"] == "COMPLETE" and receipt["exit_code"] == 0
    assert receipt["result_sha256"] == sha(HERE / (result["case"]+"_result.json"))
    assert receipt["sampled_peak_combined_rss_bytes"] < 4294967296
    assert receipt["wall_seconds"] < cap
    assert receipt["command"][0] == "/Volumes/SSD990/cryptanalysis/sage"

for name, result, protocol_name in (("n131_p_k4", positive_result, "run_protocol_n131.json"),
                                    ("n131_o_k4", public_result, "run_protocol_public.json")):
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert read(name+"_receipt.json")["protocol_sha256"] == sha(HERE / protocol_name)
assert gcd["protocol_sha256"] == sha(HERE / "w33_gcd_protocol.json")
assert direct["protocol_sha256"] == sha(HERE / "w33_direct_root_protocol.json")

verification = {"status": "PASS_NONZERO_BRANCH_TERMINAL_VERIFICATION",
                "candidate_id": None,
                "curve_id": positive_result["curve_id"],
                "n41_gate": n41["status"],
                "positive_codes": positive_result["recovered_codes"],
                "public_gcd_rejected_codes": 16,
                "positive_gcd_surviving_codes": [3],
                "positive_parent_wall_seconds": positive_receipt["wall_seconds"],
                "public_parent_wall_seconds": public_receipt["wall_seconds"],
                "protocol_sha256": sha(protocol_path),
                "verifier_sha256": sha(Path(__file__))}
(HERE/"verification_result.json").write_text(json.dumps(verification, indent=2, sort_keys=True)+"\n")
print(json.dumps(verification, sort_keys=True))
