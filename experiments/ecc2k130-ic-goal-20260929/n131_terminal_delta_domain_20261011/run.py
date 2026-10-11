"""Exact product-difference code domains for the 32-state N131 terminal pool."""

import hashlib
import json
import resource
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
POOL = ROOT / "n131_w18_terminal_fiber_20261011/pool.json"
COUNT = ROOT / "n131_w18_terminal_fiber_20261011/source_count.json"
SUPPORT = ROOT / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["status"] == "FROZEN_N131_TERMINAL_DELTA_DOMAIN"
    assert protocol["sha256"] == {
        "source": sha(Path(__file__)), "pool": sha(POOL),
        "source_count": sha(COUNT), "support": sha(SUPPORT)}
    start = time.monotonic_ns()
    pool = json.loads(POOL.read_text())
    prior = json.loads(COUNT.read_text())
    seed = pool["seed_mask"]
    pivot = seed.bit_length()-1
    source_bits = [i for i in range(18) if i != pivot]
    columns = {int(a): int(b) for a, b in
               (line.split() for line in SUPPORT.read_text().splitlines())}
    assert len(source_bits) == 17
    edges = {}
    for a, col_a in columns.items():
        b = a ^ seed
        if a >= b or b not in columns or col_a == columns[b]:
            continue
        code = sum(((a >> bit) & 1) << j for j, bit in enumerate(source_bits))
        assert code not in edges
        edges[code] = (col_a, columns[b])
    assert len(edges) == prior["eligible_unordered_source_edges"] == 33191
    by_code = {}
    for state in pool["states"]:
        code = state["code"]
        assert code in edges
        assert tuple(state["folded_columns"]) == edges[code]
        by_code.setdefault(code, []).append(state)
    assert len(by_code) == 8
    assert all(len(rows) == 4 and len({tuple(r["signs"]) for r in rows}) == 4
               for rows in by_code.values())
    domains = {}
    histogram = Counter()
    for q, states in sorted(by_code.items()):
        occupied = set(edges[q])
        domain = {p ^ q for p, pair_cols in edges.items()
                  if not occupied.intersection(pair_cols)}
        domains[q] = domain
        histogram.update(domain)
    source_rows = {tuple(row["folded_columns"]): row["remaining_edges"]
                   for row in prior["conditional_edge_rows"]}
    for q, domain in domains.items():
        assert len(domain) == source_rows[edges[q]]
    union = set.union(*domains.values())
    intersection = set.intersection(*domains.values())
    multiplicity = dict(sorted(Counter(histogram.values()).items()))
    assert sum(count*ways for count, ways in multiplicity.items()) == sum(map(len, domains.values()))
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak *= 1024
    out = {
        "status": "COMPLETE", "candidate_id": None,
        "curve_id": pool["curve_id"], "seed_mask": seed,
        "source_edges": len(edges), "terminal_signed_states": len(pool["states"]),
        "distinct_terminal_edges": len(by_code),
        "product_code_dimension": len(source_bits),
        "terminal_codes": sorted(by_code),
        "difference_domain_sizes": {str(q): len(v) for q, v in sorted(domains.items())},
        "union_size": len(union), "intersection_codes": sorted(intersection),
        "multiplicity_histogram": {str(k): v for k, v in multiplicity.items()},
        "total_allowed_edge_terminal_pairs": sum(map(len, domains.values())),
        "elapsed_ns": time.monotonic_ns()-start, "peak_rss_bytes": peak,
        "protocol_sha256": sha(HERE / "protocol.json"),
        "source_sha256": sha(Path(__file__)),
    }
    assert out["elapsed_ns"] < protocol["cap_seconds"]*10**9
    assert peak < protocol["rss_cap_bytes"]
    (HERE / "result.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
    print(json.dumps({k: out[k] for k in
                      ("status", "source_edges", "distinct_terminal_edges",
                       "union_size", "intersection_codes",
                       "total_allowed_edge_terminal_pairs")}))


if __name__ == "__main__":
    main()
