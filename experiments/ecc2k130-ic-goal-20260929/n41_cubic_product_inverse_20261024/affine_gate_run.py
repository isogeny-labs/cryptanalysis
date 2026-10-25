#!/usr/bin/env sage -python
"""Lossless two-half affine-span gate for the frozen N41 four-code traversal."""

import hashlib
import importlib.util
import json
import time
from collections import Counter
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GEOMETRY = ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json"
CASES = ROOT / "n41_w8_two_code_affine_span_20261013/cases.jsonl"
TABLE = ROOT / "n41_four_code_suffix_quotient_20261024/target_table.json"
CURVE = ROOT / "n41_w8_fixed_sum_table_20261009/audit.py"
PROTOCOL = HERE / "affine_gate_protocol.json"
RESULT = HERE / "affine_gate_result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def insert(pivots, value):
    """Insert one vector into a GF(2) row-echelon basis, returning its novelty."""
    while value:
        bit = value.bit_length() - 1
        if pivots[bit]:
            value ^= pivots[bit]
        else:
            pivots[bit] = value
            return True
    return False


def contained(pivots, value):
    while value:
        bit = value.bit_length() - 1
        if not pivots[bit]:
            return False
        value ^= pivots[bit]
    return True


def main():
    protocol = json.loads(PROTOCOL.read_text())
    inputs = {"geometry": GEOMETRY, "cases": CASES, "table": TABLE,
              "curve": CURVE, "producer": Path(__file__)}
    assert {name: sha(path) for name, path in inputs.items()} == protocol["sha256"]
    assert sha(HERE / "affine_gate_runtime_info.json") == protocol["sage_runtime_sha256"]
    assert not RESULT.exists(), "refusing to overwrite the frozen result"

    setup_start = time.monotonic_ns()
    spec = importlib.util.spec_from_file_location("n41_curve_audit", CURVE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    curve, elem, integer = module.sage_curve()
    geo = json.loads(GEOMETRY.read_text())
    table = json.loads(TABLE.read_text())
    assert geo["curve_id"] == table["curve_id"] == protocol["curve_id"]
    assert len(table["rows"]) == 40 and all(len(row) == 4 for row in table["rows"])
    assert table["suffix_state_ids"] == [14, 109, 51]
    third = geo["blocks"][2]
    basis = [elem(x) for x in third["product_basis"]]
    basis_sq = [x*x for x in basis]
    source_products = {}
    for code in range(40):
        state = third["states"][4*code]
        value = 0
        for index, raw in enumerate(third["product_basis"]):
            if state["a"] >> index & 1:
                value ^= raw
        assert value not in source_products
        source_products[value] = code
    assert len(source_products) == 40
    product_pivots = [0]*41
    product_rank = sum(insert(product_pivots, int(x)) for x in third["product_basis"])
    cases = []
    with CASES.open() as stream:
        for line in stream:
            row = json.loads(line)
            roots = []
            for raw in row["reciprocal_coordinates"]:
                v = elem(raw)
                assert v != 1
                u = v/(v+1)
                roots.append((u*u, (u+1)**2, u*(u+1)))
            assert len(roots) == 8
            cases.append((row["left_code"], row["right_code"], roots))
    assert len(cases) == 1554
    seed_sq = elem(third["s"])**2
    one = elem(1)
    zero = elem(0)
    setup_ns = time.monotonic_ns()-setup_start

    half_survivors = [0, 0]
    half_ranks = [Counter(), Counter()]
    source_hits = []
    charts = 0
    family_count = 0
    retained = 0
    target_start = time.monotonic_ns()
    for row in table["rows"]:
        for chart in row:
            state_id = chart["state_id"]
            t = elem(chart["chart"])
            t2, tp12, tau = t*t, (t+one)**2, t*(t+one)
            charts += 1
            for left, right, roots in cases:
                family_count += 1
                coefficients = []
                for u2, up12, utau in roots:
                    A = t2+utau*tau+tp12
                    B = utau*tau
                    D = up12*t2+u2*tp12
                    c0 = (D+seed_sq*A)**2+seed_sq*B**2
                    c1 = B*(D+seed_sq*(A+B))
                    c2 = D*(A+B+D)
                    coefficients.append((c0,c1,c2))
                survived = False
                for half in range(2):
                    values = coefficients[4*half:4*half+4]
                    anchor = integer(values[0][0])
                    pivots = [0]*41
                    rank = 0
                    for index, (c0,c1,c2) in enumerate(values):
                        if index:
                            rank += insert(pivots, integer(c0)^anchor)
                        for b, b2 in zip(basis, basis_sq):
                            rank += insert(pivots, integer(c1*b+c2*b2))
                    half_ranks[half][rank] += 1
                    if contained(pivots, anchor):
                        half_survivors[half] += 1
                        survived = True
                if not survived:
                    continue
                retained += 1
                for root_index, (c0,c1,c2) in enumerate(coefficients):
                    for product, code in source_products.items():
                        p = elem(product)
                        if c0+c1*p+c2*p*p == zero:
                            source_hits.append([state_id,left,right,root_index,code])
    target_ns = time.monotonic_ns()-target_start
    assert charts == 160 and family_count == 160*1554
    assert product_rank == 7
    assert source_hits == [[0,24,37,2,10]], source_hits

    # Independent point and folded-column replay of the retained witness.
    witness_ids = [97,151,42,0,14,109,51]
    total = curve(0)
    columns = []
    for axis, sid in enumerate(witness_ids):
        state = geo["blocks"][axis]["states"][sid]
        total += curve(*(elem(x) for x in state["raw_sum"]))
        columns.extend(state["columns"])
    expected = curve(*(elem(x) for x in table["raw_target"]))
    assert total == expected and len(columns) == len(set(columns)) == 14

    result = {
        "status": "PASS_N41_FOUR_AXIS_TWO_HALF_AFFINE_GATE",
        "candidate_id": None,
        "curve_id": geo["curve_id"],
        "charts": charts,
        "families": family_count,
        "source_product_span_rank": product_rank,
        "half_survivors": half_survivors,
        "half_rank_histograms": [dict(sorted(x.items())) for x in half_ranks],
        "families_retained": retained,
        "source_product_hits": source_hits,
        "witness_state_ids": witness_ids,
        "witness_folded_columns": len(columns),
        "setup_ns": setup_ns,
        "target_dependent_ns": target_ns,
        "peak_process_rss_sample_bytes": psutil.Process().memory_info().rss,
        "protocol_sha256": sha(PROTOCOL),
    }
    RESULT.write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")
    print(json.dumps({key: result[key] for key in
          ("status", "charts", "families", "half_survivors", "families_retained",
           "source_product_hits", "target_dependent_ns")}, sort_keys=True))


if __name__ == "__main__":
    main()
