"""Independent field-product and bitset replay of terminal delta domains."""

import hashlib
import importlib.util
import json
import resource
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PAIR = ROOT / "n131_fixed_seed_eight_pair_circuit_20261010/fixed_pair_circuit.py"
SUPPORT_CODE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011/support.py"
SUPPORT = ROOT / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
POOL = ROOT / "n131_w18_terminal_fiber_20261011/pool.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rank(values):
    pivots = {}
    for value in values:
        while value:
            lead = value.bit_length()-1
            if lead in pivots:
                value ^= pivots[lead]
            else:
                pivots[lead] = value
                break
    return len(pivots)


def main():
    p = json.loads((HERE / "audit_protocol.json").read_text())
    assert p["status"] == "FROZEN_N131_TERMINAL_DELTA_AUDIT"
    assert p["sha256"] == {
        "source": sha(Path(__file__)), "producer": sha(HERE / "result.json"),
        "pair": sha(PAIR), "support_code": sha(SUPPORT_CODE),
        "support": sha(SUPPORT), "pool": sha(POOL)}
    expected = json.loads((HERE / "result.json").read_text())
    pair = load("n131_delta_pair", PAIR)
    support = load("n131_delta_support", SUPPORT_CODE)
    columns = support.columns_from(SUPPORT)
    codes = pair.valid_codes(columns)
    states = json.loads(POOL.read_text())["states"]
    q_codes = sorted({row["code"] for row in states})
    assert len(codes) == 33191 and len(q_codes) == 8
    assert rank(pair.product_basis()) == 17
    start = time.monotonic_ns()
    products = {}
    seed = pair.coordinate(pair.SEED)
    for code in codes:
        w = pair.coordinate(pair.mask_from_code(code))
        product = pair.product_from_code(code)
        assert product == pair.gf_square(w) ^ pair.gf_mul(seed, w)
        products[code] = product
    assert len(set(products.values())) == len(codes)
    counts = [0] * (1 << 17)
    sizes = {}
    for q in q_codes:
        assert q in codes
        a = pair.mask_from_code(q)
        occupied = {columns[a], columns[a ^ pair.SEED]}
        n = 0
        for c in codes:
            a = pair.mask_from_code(c)
            if occupied.intersection((columns[a], columns[a ^ pair.SEED])):
                continue
            delta = c ^ q
            assert products[c] ^ products[q] == pair.product_from_code(delta)
            counts[delta] += 1
            n += 1
        sizes[str(q)] = n
    histogram = {str(k): v for k, v in sorted(Counter(x for x in counts if x).items())}
    assert sizes == expected["difference_domain_sizes"]
    assert histogram == expected["multiplicity_histogram"]
    assert sum(x > 0 for x in counts) == expected["union_size"]
    assert [i for i, count in enumerate(counts) if count == 8] == expected["intersection_codes"]
    assert sum(counts) == expected["total_allowed_edge_terminal_pairs"]
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak *= 1024
    out = {"status": "PASS_INDEPENDENT_FIELD_DELTA_AUDIT",
           "source_product_basis_rank": 17,
           "source_products_checked": len(codes),
           "field_difference_checks": sum(counts),
           "union_size": expected["union_size"],
           "intersection_codes": expected["intersection_codes"],
           "elapsed_ns": time.monotonic_ns()-start,
           "peak_rss_bytes": peak,
           "protocol_sha256": sha(HERE / "audit_protocol.json")}
    assert out["elapsed_ns"] < p["cap_seconds"]*10**9
    assert peak < p["rss_cap_bytes"]
    (HERE / "audit.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
    print(json.dumps({k: out[k] for k in
                      ("status", "source_products_checked", "field_difference_checks",
                       "union_size", "intersection_codes")}))


if __name__ == "__main__":
    main()
