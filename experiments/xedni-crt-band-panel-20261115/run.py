"""Deterministic subgroup-band selection and frozen CRT target replay."""

import hashlib
import importlib.util
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, ZZ, prime_range

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "xedni-crt-prime-panel-20261115" / "run.py"
spec = importlib.util.spec_from_file_location("xedni_crt_prime_panel", PARENT)
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    protocol_path = HERE / "protocol.json"
    protocol = json.loads(protocol_path.read_text())
    assert protocol["schema"] == "xedni-crt-band-panel-protocol-v1"
    assert sha(PARENT.read_bytes()) == protocol["parent_run_source_sha256"]
    assert sha(panel.PARENT.read_bytes()) == protocol["grandparent_search_source_sha256"]
    rule = protocol["field_selection"]
    lower, upper = rule["scan_primes_inclusive"]
    selected = []
    selection_rows = []
    for p in prime_range(lower, upper + 1):
        p = int(p)
        if panel.parent.delta(0, 0, 0, -1, -2) % p == 0:
            selection_rows.append({"field_prime": p, "status": "singular_base_curve"})
            continue
        curve = EllipticCurve(GF(p), protocol["base_curve_coefficients"])
        order = int(curve.cardinality())
        r = max(int(factor) for factor, _ in ZZ(order).factor())
        eligible = 43 <= r <= 80
        selection_rows.append({"field_prime": p, "curve_order": order,
                               "largest_prime_factor": r, "selected": eligible})
        if eligible:
            selected.append(p)
        if len(selected) == rule["expected_number_of_fields"]:
            break
    selection = {"schema": "xedni-crt-band-selection-v1",
                 "protocol_sha256": sha(protocol_path.read_bytes()),
                 "source_sha256": sha(Path(__file__).read_bytes()),
                 "selected_primes": selected, "screened_primes": selection_rows}
    (HERE / "selection.json").write_text(json.dumps(selection, sort_keys=True, indent=2) + "\n")
    if len(selected) != rule["expected_number_of_fields"]:
        print(json.dumps({"schema": "xedni-crt-band-panel-result-v1",
                          "status": "insufficient_eligible_fields", "selected_primes": selected},
                         sort_keys=True, indent=2))
        return
    orders = {l: panel.parent.coefficient_order(l) for l in (7, 11)}
    characters = {l: panel.character_table(l) for l in (7, 11)}
    projected_queries = sum(next(row["largest_prime_factor"] for row in selection_rows
                                 if row["field_prime"] == p) ** 2 for p in selected)
    if projected_queries > protocol["max_total_target_queries"]:
        print(json.dumps({"schema": "xedni-crt-band-panel-result-v1",
                          "status": "query_cap", "projected_queries": projected_queries},
                         sort_keys=True, indent=2))
        return
    panel.HERE = HERE
    fields = [panel.run_prime(p, protocol, orders, characters) for p in selected]
    assert all(field["status"] == "PASS" for field in fields)
    result = {"schema": "xedni-crt-band-panel-result-v1", "status": "PASS",
              "protocol_sha256": sha(protocol_path.read_bytes()),
              "source_sha256": sha(Path(__file__).read_bytes()),
              "selection_sha256": sha((HERE / "selection.json").read_bytes()),
              "parent_run_source_sha256": sha(PARENT.read_bytes()),
              "grandparent_search_source_sha256": sha(panel.PARENT.read_bytes()),
              "sage_runtime_sha256": sha((HERE / "sage-runtime-info.json").read_bytes()),
              "projected_queries": projected_queries, "fields": fields}
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
