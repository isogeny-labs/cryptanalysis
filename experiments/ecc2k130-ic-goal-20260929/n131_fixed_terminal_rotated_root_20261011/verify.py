"""Verify frozen fixed-terminal root and independent audit receipts."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def sha(name):
    return hashlib.sha256((HERE / name).read_bytes()).hexdigest()


def main():
    failed = read("failure_v1.json")
    assert failed["status"] == "PRODUCER_FAILURE"
    assert failed["scientific_decision"] is None
    for key, name in (("source_sha256", "run.py"),
                      ("protocol_sha256", "protocol.json"),
                      ("stderr_sha256", "run.stderr.txt")):
        assert failed[key] == sha(name)

    protocol, result = read("protocol_v2.json"), read("result_v2.json")
    ap, audit = read("audit_protocol.json"), read("audit.json")
    assert result["status"] == "COMPLETE" and result["candidate_id"] is None
    assert audit["status"] == "PASS_INDEPENDENT_FIXED_TERMINAL_FIELD_SCAN"
    assert result["protocol_sha256"] == sha("protocol_v2.json")
    assert result["source_sha256"] == sha("run_v2.py")
    assert audit["protocol_sha256"] == sha("audit_protocol.json")
    assert protocol["sha256"]["source"] == sha("run_v2.py")
    assert protocol["sha256"]["runtime"] == sha("sage_runtime_info.json")
    assert ap["sha256"]["source"] == sha("audit.py")
    assert ap["sha256"]["producer"] == sha("result_v2.json")
    assert protocol["curve_id"] == result["curve_id"] == audit["curve_id"]
    assert protocol["workers"] == ap["workers"] == 1
    assert result["source_products"] == audit["source_products"] == 33188
    assert result["first_product_positive"] == audit["positive_product"] == 3328
    assert result["peak_rss_bytes"] < protocol["rss_cap_bytes"]
    assert audit["peak_rss_bytes"] < ap["rss_cap_bytes"]
    expected = {"constructed_positive": [[3328, 4]],
                "field_control": [], "frozen_public_residual": []}
    for name, hits in expected.items():
        producer = result["cases"][name]
        checker = audit["cases"][name]
        assert producer["degree"] == 4 and len(producer["field_roots"]) == 4
        assert producer["source_supported_products_and_codes"] == hits
        assert checker["source_hits"] == hits
        assert checker["source_products_checked"] == 33188
        assert producer["query_ns"] < protocol["cap_seconds_per_case"] * 10**9
        assert checker["scan_ns"] < ap["cap_seconds_per_case"] * 10**9
    assert not (HERE / "run_v2.stderr.txt").read_bytes()
    assert not (HERE / "audit.stderr.txt").read_bytes()
    print(json.dumps({"status": "PASS_FROZEN_FIXED_TERMINAL_ROOT",
                      "source_products_per_case": 33188,
                      "source_hits": {name: hits for name, hits in expected.items()},
                      "v1_status": failed["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
