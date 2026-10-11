"""Bind exact source-code and independent field audits for delta coverage."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
POOL = ROOT / "n131_w18_terminal_fiber_20261011/pool.json"
COUNT = ROOT / "n131_w18_terminal_fiber_20261011/source_count.json"
SUPPORT = ROOT / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
PAIR = ROOT / "n131_fixed_seed_eight_pair_circuit_20261010/fixed_pair_circuit.py"
SUPPORT_CODE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011/support.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    p, a = read("protocol.json"), read("audit_protocol.json")
    result, audit = read("result.json"), read("audit.json")
    assert p["status"] == "FROZEN_N131_TERMINAL_DELTA_DOMAIN"
    assert p["sha256"] == {
        "source": sha(HERE / "run.py"), "pool": sha(POOL),
        "source_count": sha(COUNT), "support": sha(SUPPORT)}
    assert a["status"] == "FROZEN_N131_TERMINAL_DELTA_AUDIT"
    assert a["sha256"] == {
        "source": sha(HERE / "audit.py"), "producer": sha(HERE / "result.json"),
        "pair": sha(PAIR), "support_code": sha(SUPPORT_CODE),
        "support": sha(SUPPORT), "pool": sha(POOL)}
    assert result["status"] == "COMPLETE"
    assert audit["status"] == "PASS_INDEPENDENT_FIELD_DELTA_AUDIT"
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["source_sha256"] == sha(HERE / "run.py")
    assert audit["protocol_sha256"] == sha(HERE / "audit_protocol.json")
    assert result["curve_id"] == p["curve_id"] == "EC1N131Ckb1heb5f1998f20b"
    assert result["source_edges"] == audit["source_products_checked"] == 33191
    assert result["terminal_signed_states"] == 32
    assert result["distinct_terminal_edges"] == 8
    assert result["product_code_dimension"] == audit["source_product_basis_rank"] == 17
    assert result["terminal_codes"] == [4, 10, 17, 18, 22, 24, 28, 29]
    assert min(result["difference_domain_sizes"].values()) == 33188
    assert max(result["difference_domain_sizes"].values()) == 33190
    assert result["union_size"] == audit["union_size"] == 118107
    assert result["intersection_codes"] == audit["intersection_codes"] == [52475]
    assert result["total_allowed_edge_terminal_pairs"] == audit["field_difference_checks"] == 265509
    assert sum(int(k)*v for k, v in result["multiplicity_histogram"].items()) == 265509
    assert sum(result["multiplicity_histogram"].values()) == 118107
    assert result["elapsed_ns"] < p["cap_seconds"]*10**9
    assert audit["elapsed_ns"] < a["cap_seconds"]*10**9
    assert result["peak_rss_bytes"] < p["rss_cap_bytes"]
    assert audit["peak_rss_bytes"] < a["rss_cap_bytes"]
    out = {"status": "PASS_N131_TERMINAL_DELTA_BOUNDARY",
           "source_edges": 33191, "terminal_edges": 8,
           "difference_code_space": 131072, "union_size": 118107,
           "per_terminal_min": 33188, "per_terminal_max": 33190,
           "producer_sha256": sha(HERE / "result.json"),
           "audit_sha256": sha(HERE / "audit.json")}
    (HERE / "verification.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
