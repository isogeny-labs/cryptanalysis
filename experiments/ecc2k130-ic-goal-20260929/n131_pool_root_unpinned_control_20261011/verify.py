"""Check frozen pool-root controls and independent N131 bit-field scan."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
INPUTS = {
    "source": HERE / "run.py",
    "runtime": HERE / "sage_runtime_info.json",
    "n41_rows": ROOT / "n41_w8_terminal32_sevenpair_20261011/sage_audit_result.json",
    "n41_geometry": ROOT / "n41_w7_entropy_cubic_20261011/w8/geometry.json",
    "n41_fixture": ROOT / "n41_w7_entropy_cubic_20261011/w8/fixture.json",
    "n41_query": ROOT / "n41_w8_terminal32_sevenpair_20261011/query_result.json",
    "n131_root": ROOT / "n131_fixed_terminal_rotated_root_20261011/result_v2.json",
    "n131_audit": ROOT / "n131_fixed_terminal_rotated_root_20261011/audit.json",
    "n131_pool": ROOT / "n131_w18_terminal_fiber_20261011/pool.json",
    "n131_pair": ROOT / "n131_fixed_seed_eight_pair_circuit_20261010/fixed_pair_circuit.py",
    "n131_support": ROOT / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv",
}
AUDIT_INPUTS = {"source": HERE / "audit.py", "producer": HERE / "result.json",
                "pair": INPUTS["n131_pair"], "support": INPUTS["n131_support"],
                "pool": INPUTS["n131_pool"],
                "root_audit": INPUTS["n131_audit"]}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    protocol, result = read("protocol.json"), read("result.json")
    audit_protocol, audit = read("audit_protocol.json"), read("audit_result.json")
    assert protocol["status"] == "FROZEN_UNPINNED_N41_AND_N131_POOL_ROOT"
    assert audit_protocol["status"] == "FROZEN_POOL_BITFIELD_AUDIT"
    assert protocol["sha256"] == {name: sha(path) for name, path in INPUTS.items()}
    assert audit_protocol["sha256"] == {name: sha(path) for name, path in AUDIT_INPUTS.items()}
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert audit["protocol_sha256"] == sha(HERE / "audit_protocol.json")
    assert result["status"] == "PASS_UNPINNED_N41_AND_N131_POOL_ROOT"
    assert audit["status"] == "PASS_INDEPENDENT_EIGHT_EDGE_BITFIELD_SCAN"
    assert result["candidate_id"] is None
    assert protocol["workers"] == audit_protocol["workers"] == 1
    assert result["elapsed_ns_exploratory"] < protocol["parent_cap_seconds"]*10**9
    assert result["peak_rss_bytes"] < protocol["rss_cap_bytes"]
    assert audit["peak_rss_bytes"] < audit_protocol["rss_cap_bytes"]
    assert not (HERE / "run.stderr.txt").read_bytes()
    assert not (HERE / "audit.stderr.txt").read_bytes()
    assert result["n41"]["verified_relation_count"] == result["n41"]["novel_rank"] == 2
    assert len(result["n41"]["cases"]) == 2
    expected_n41 = [(13, 5, 32272), (17, 2, 62708)]
    for case, (first, terminal, product) in zip(result["n41"]["cases"], expected_n41):
        assert (case["first_edge"], case["terminal_edge"], case["first_product"]) == (first, terminal, product)
        assert len(case["pool"]) == 8
        assert all(row["source_size"] == 34 and row["field_roots"] == 4
                   for row in case["pool"])
        assert [(row["terminal_edge"], hit) for row in case["pool"]
                for hit in row["source_hits"]] == [(terminal, [product, first])]
    assert result["n131"]["curve_id"] == audit["curve_id"]
    assert len(result["n131"]["pool"]) == len(audit["rows"]) == 8
    assert sum(row["source_size"] for row in audit["rows"]) == 265509
    for row, checked in zip(result["n131"]["pool"], audit["rows"]):
        assert row["terminal_code"] == checked["terminal_code"]
        assert row["source_size"] == checked["source_size"]
        assert row["source_hits"] == checked["source_hits"]
        assert row["field_roots"] == 4 and checked["polynomial_degree"] == 4
        assert checked["scan_ns"] < audit_protocol["cap_seconds_per_edge"]*10**9
    assert [(row["terminal_code"], hit) for row in audit["rows"]
            for hit in row["source_hits"]] == [(10, [3328, 4])]
    print(json.dumps({"status": "PASS_FROZEN_POOL_ROOT_RECEIPTS",
                      "n41_ordinary_relations": 2,
                      "n131_independently_checked_products": 265509,
                      "n131_pool_hits": 1}, sort_keys=True))


if __name__ == "__main__":
    main()
