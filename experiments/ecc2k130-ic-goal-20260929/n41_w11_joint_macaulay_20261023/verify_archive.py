"""Read-only verification of frozen N41 joint/block Macaulay evidence."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def protocol(name):
    cfg = json.loads((HERE / name).read_text())
    for label, item in cfg["sources"].items():
        assert sha(item["path"]) == item["sha256"], (name, label)
    assert cfg["candidate_id"] is None
    return cfg


whole_cfg = protocol("protocol.json")
block_cfg = protocol("block_protocol.json")
audit_cfg = protocol("audit_protocol.json")
assert whole_cfg["degrees"] == [4, 5, 6]
assert block_cfg["block_widths"] == [0, 1, 2, 3, 4]
assert block_cfg["degrees"] == [3, 4, 5, 6]
assert all(cfg["rss_cap_bytes"] == 4294967296 for cfg in
           (whole_cfg, block_cfg, audit_cfg))

whole = json.loads((HERE / "result.json").read_text())
assert whole["status"] == "COMPLETE_N41_JOINT_MACAULAY_PANEL"
assert whole["protocol_sha256"] == sha(HERE / "protocol.json")
assert whole["script_sha256"] == sha(HERE / "run.py")
assert len(whole["rows"]) == 6
for row in whole["rows"]:
    assert row["reject"] is False and row["certificate_rows"] is None
    assert row["rank"] == row["equations"]
    assert row["coefficient_terms"] == 3046

blocks = json.loads((HERE / "block_result.json").read_text())
assert blocks["status"] == "COMPLETE_N41_MACAULAY_BLOCK_PANEL"
assert blocks["protocol_sha256"] == sha(HERE / "block_protocol.json")
assert blocks["script_sha256"] == sha(HERE / "run_blocks.py")
for row in blocks["rows"]:
    if row["target_index"] == 0:
        assert row["reject"] is False and row["valid_hits"] == [[253, 63]]
    else:
        assert row["valid_hits"] == []
public_certs = [row for row in blocks["rows"] if row["target_index"] == 1 and row["reject"]]
assert [row["block_width"] for row in public_certs] == [0, 1, 2, 3, 4]
assert [row["degree"] for row in public_certs] == [3, 4, 6, 6, 6]
assert [len(row["certificate_rows"]) for row in public_certs] == [101, 166, 768, 1322, 1961]

audit = json.loads((HERE / "audit_result.json").read_text())
assert audit["status"] == "PASS_N41_BLOCK_CERTIFICATE_EXHAUSTIVE_AUDIT"
assert audit["protocol_sha256"] == sha(HERE / "audit_protocol.json")
assert audit["script_sha256"] == sha(HERE / "audit_blocks.py")
assert [row["raw_assignments_checked"] for row in audit["rows"]] == [1024, 2048, 4096, 8192, 16384]
assert all(row["raw_roots"] == 0 for row in audit["rows"])
for check, cert in zip(audit["rows"], public_certs):
    assert check["block_width"] == cert["block_width"]
    assert check["certificate_rows"] == len(cert["certificate_rows"])

census = json.loads(Path(whole_cfg["sources"]["complete_census"]["path"]).read_text())
assert census["status"] == "COMPLETE_N41_W11_FREECODE_RESULTANT_CENSUS"
assert census["rows"][0]["zero_pairs"] == [[253, 63]]
assert census["rows"][1]["zero_pairs"] == []
proof = (HERE / "lean_check.txt").read_text()
assert "MacaulayBlockSound.constant_one_block_certificate_sound" in proof
assert "[propext, Classical.choice, Quot.sound]" in proof
lean_source = (HERE / "MacaulayBlockSound.lean").read_text()
assert "#print axioms constant_one_block_certificate_sound" in lean_source
assert not any(word in lean_source for word in ("sorry", "admit", "sorryAx", "native_decide"))
print("PASS_N41_JOINT_MACAULAY_ARCHIVE")
