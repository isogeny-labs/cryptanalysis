"""Read-only verification of W20 root-function screen receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name):
    return json.loads((HERE / name).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_protocol(name):
    record = load(name)
    for path, digest in record["sources"].items():
        assert sha(path) == digest, (name, path)
    assert record["candidate_id"] is None
    assert record["worker_count"] == 1
    assert record["wall_cap_seconds"] == 180
    assert record["rss_cap_bytes"] == 4294967296
    return record


def main():
    primary = check_protocol("protocol.json")
    check_protocol("audit_protocol.json")
    runtime = load("sage_runtime_info.json")
    assert runtime["status"] == "verified"
    result = load("result.json")
    audit = load("audit_result.json")
    assert result["status"] == "PASS_W20_ROOT_FUNCTION_SUBCUBE_BDD_SCREEN"
    assert audit["status"] == "PASS_INDEPENDENT_SAGE_W20_ROOT_BDD_SUBCUBE"
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert audit["protocol_sha256"] == sha(HERE / "audit_protocol.json")
    assert result["valid_codes_full_domain"] == 132045
    assert result["candidate_id"] is audit["candidate_id"] is None
    assert result["wall_ns"] < primary["wall_cap_seconds"] * 10**9
    assert audit["wall_ns"] < primary["wall_cap_seconds"] * 10**9
    assert result["peak_process_rss_sample_bytes"] < primary["rss_cap_bytes"]
    assert audit["peak_process_rss_sample_bytes"] < primary["rss_cap_bytes"]
    assert (HERE / "screen.stdout").read_text().strip() == "PASS_W20_ROOT_FUNCTION_SUBCUBE_BDD_SCREEN 16548 16"
    assert (HERE / "audit.stdout").read_text().strip() == "PASS_INDEPENDENT_SAGE_W20_ROOT_BDD_SUBCUBE 4184 8"
    assert not (HERE / "screen.stderr").read_text()
    assert not (HERE / "audit.stderr").read_text()

    rows = result["records"]
    assert len(rows) == 16
    assert [(x["prefix_m14"], x["bit_count"]) for x in rows] == [
        (prefix, bits) for prefix in primary["prefixes_m14"]
        for bits in primary["subcube_bit_counts"]]
    assert primary["prefixes_m14"] == [0, 8, 16, 24]
    assert primary["subcube_bit_counts"] == [8, 10, 12, 14]
    assert all(0 < x["valid_codes"] < 1 << x["bit_count"] for x in rows)
    assert all(x["undefined_output_bits"] == [0, 0] for x in rows)
    m14 = [x for x in rows if x["bit_count"] == 14]
    assert [x["valid_codes"] for x in m14] == [4184, 4126, 4121, 4117]
    assert [x["halftrace_root_shared_nodes"] for x in m14] == [94470, 94373, 93961, 93260]
    assert [x["canonical_root_shared_nodes"] for x in m14] == [94492, 94355, 93897, 93094]
    assert result["root_codes_computed"] == sum(x["valid_codes"] for x in m14) == 16548
    assert result["witness_code"] == 3
    assert result["witness_canonical_root"] > 0
    assert result["witness_halftrace_root"] > 0
    row = m14[0]
    assert audit["prefix_m14"] == 0 and audit["bit_count"] == 14
    assert audit["valid_codes"] == row["valid_codes"]
    assert audit["direct_group_codes_checked"] == 8
    assert audit["halftrace_bdd_nodes"] == row["halftrace_root_shared_nodes"]
    assert audit["canonical_bdd_nodes"] == row["canonical_root_shared_nodes"]
    print("PASS_W20_ROOT_BDD_RECEIPT_VERIFICATION", len(rows), result["root_codes_computed"])


if __name__ == "__main__":
    main()
