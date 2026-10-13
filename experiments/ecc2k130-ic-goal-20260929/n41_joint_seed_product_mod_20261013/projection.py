"""Exact dense-memory and decision-count gate for a literal W18 transfer."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SUPPORT = GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = json.loads((HERE / "projection_protocol.json").read_text())
    paths = {"script": HERE / "projection.py", "support": SUPPORT,
             "n41_global": HERE / "global_result.json",
             "n41_search": HERE / "search_result.json",
             "n41_audit": HERE / "audit_result.json"}
    assert {key: sha(path) for key, path in paths.items()} == p["sha256"]
    rows = [line.split() for line in SUPPORT.read_text().splitlines()]
    assert len(rows) == 131307 and all(len(row) == 2 for row in rows)
    w, n = p["source_width"], p["field_degree"]
    assert w == 18 and n == 131 and 2 * w < n
    seeds = (1 << w) - 1
    bucket_degree = 1 << w
    global_degree = seeds * bucket_degree
    coefficient_count = global_degree + 1
    one_bit_dense_bytes = (coefficient_count + 7) // 8
    full_dense_bytes = (coefficient_count * n + 7) // 8
    decisions = seeds * p["raw_fiber_count"]
    result = {"status": "PASS_EXACT_LITERAL_W18_GLOBAL_PRODUCT_RESOURCE_GATE",
              "candidate_id": None, "curve_id": p["curve_id"],
              "source_width": w, "field_degree": n,
              "rational_supported_masks": len(rows),
              "unfiltered_nonzero_seed_count": seeds,
              "unfiltered_bucket_degree": bucket_degree,
              "unfiltered_global_polynomial_degree": global_degree,
              "dense_coefficient_count": coefficient_count,
              "dense_one_bit_per_coefficient_bytes": one_bit_dense_bytes,
              "dense_full_field_coefficient_bytes": full_dense_bytes,
              "raw_fiber_count": p["raw_fiber_count"],
              "literal_seed_fiber_gcd_decisions": decisions,
              "decisions_per_second_needed_for_600_seconds":
                  (decisions + p["wall_cap_seconds"] - 1) // p["wall_cap_seconds"],
              "rss_cap_bytes": p["rss_cap_bytes"],
              "protocol_sha256": sha(HERE / "projection_protocol.json")}
    with (HERE / "projection_result.json").open("x") as out:
        out.write(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in
                      ("unfiltered_global_polynomial_degree",
                       "dense_full_field_coefficient_bytes",
                       "literal_seed_fiber_gcd_decisions")}, sort_keys=True))


if __name__ == "__main__":
    main()
