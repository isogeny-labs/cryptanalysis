"""Independent field selection and exact-row replay for the subgroup-band panel."""

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT_AUDIT = HERE.parent / "xedni-crt-prime-panel-20261115" / "audit.py"
PARENT_RUN = HERE.parent / "xedni-crt-prime-panel-20261115" / "run.py"
spec = importlib.util.spec_from_file_location("xedni_crt_prime_audit", PARENT_AUDIT)
panel_audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel_audit)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def is_prime(n):
    return n >= 2 and all(n % d for d in range(2, int(n ** 0.5) + 1))


def main():
    protocol_path = HERE / "protocol.json"
    protocol = json.loads(protocol_path.read_text())
    selection_path = HERE / "selection.json"
    selection = json.loads(selection_path.read_text())
    result = json.loads((HERE / "result.json").read_text())
    assert protocol["schema"] == "xedni-crt-band-panel-protocol-v1"
    assert sha(PARENT_AUDIT.read_bytes()) == protocol["parent_audit_source_sha256"]
    assert sha(PARENT_RUN.read_bytes()) == protocol["parent_run_source_sha256"]
    assert sha(panel_audit.PRIOR_AUDIT.read_bytes()) == \
        "565365e0e9093dcc512cc551bb19760b4f6aa54538093c557dc1acd1cdf645f7"
    assert result["status"] == "PASS"
    assert result["protocol_sha256"] == sha(protocol_path.read_bytes())
    assert result["source_sha256"] == sha((HERE / "run.py").read_bytes())
    assert result["selection_sha256"] == sha(selection_path.read_bytes())
    assert result["sage_runtime_sha256"] == sha((HERE / "sage-runtime-info.json").read_bytes())
    assert result["parent_run_source_sha256"] == protocol["parent_run_source_sha256"]
    assert result["grandparent_search_source_sha256"] == protocol["grandparent_search_source_sha256"]
    assert selection["protocol_sha256"] == result["protocol_sha256"]
    assert selection["source_sha256"] == result["source_sha256"]

    rule = protocol["field_selection"]
    lower, upper = rule["scan_primes_inclusive"]
    expected_rows = []
    selected = []
    base = protocol["base_curve_coefficients"]
    for p in range(lower, upper + 1):
        if not is_prime(p):
            continue
        if panel_audit.delta(base) % p == 0:
            expected_rows.append({"field_prime": p, "status": "singular_base_curve"})
            continue
        order = len(panel_audit.field_points(p, base)) + 1
        r = panel_audit.largest_prime_factor(order)
        eligible = 43 <= r <= 80
        expected_rows.append({"field_prime": p, "curve_order": order,
                              "largest_prime_factor": r, "selected": eligible})
        if eligible:
            selected.append(p)
        if len(selected) == rule["expected_number_of_fields"]:
            break
    assert selection["screened_primes"] == expected_rows
    assert selection["selected_primes"] == selected
    assert [field["field_prime"] for field in result["fields"]] == selected
    assert sum(field["subgroup_order"] ** 2 for field in result["fields"]) == \
        result["projected_queries"] <= protocol["max_total_target_queries"]
    assert set((HERE / "rows").glob("*.jsonl.gz")) == {
        HERE / "rows" / shard for field in result["fields"] for shard in field["row_shards"]}

    orders = {prime: panel_audit.prior.candidates(prime) for prime in (7, 11)}
    chars = {}
    for prime in orders:
        squares = {x * x % prime for x in range(1, prime)}
        chars[prime] = [0 if x == 0 else 1 if x in squares else -1
                        for x in range(prime)]
    panel_audit.HERE = HERE
    total = sum(panel_audit.check_prime(record, protocol, orders, chars)
                for record in result["fields"])
    assert total == result["projected_queries"]

    earlier = json.loads((HERE.parent / "xedni-crt-prime-panel-20261115" / "result.json").read_text())
    earlier_by_prime = {field["field_prime"]: field for field in earlier["fields"]}
    for record in result["fields"]:
        if record["field_prime"] in earlier_by_prime:
            reference = earlier_by_prime[record["field_prime"]]
            assert record["counts"] == reference["counts"]
            assert record["rows_sha256"] == reference["rows_sha256"]
            assert record["first_rational_relation"] == reference["first_rational_relation"]

    print(json.dumps({"schema": "xedni-crt-band-panel-audit-v1", "status": "PASS",
                      "source_sha256": sha(Path(__file__).read_bytes()),
                      "parent_audit_source_sha256": sha(PARENT_AUDIT.read_bytes()),
                      "selected_primes": selected, "queries_audited": total,
                      "reproduced_reference_primes": [47, 101]}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
