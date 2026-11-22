#!/usr/bin/env sage -python
"""Independent receipt and exact witness check for the N41 affine gate."""

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GEOMETRY = ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json"
CASES = ROOT / "n41_w8_two_code_affine_span_20261013/cases.jsonl"
TABLE = ROOT / "n41_four_code_suffix_quotient_20261024/target_table.json"
CURVE = ROOT / "n41_w8_fixed_sum_table_20261009/audit.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "affine_gate_protocol.json").read_text())
    result = json.loads((HERE / "affine_gate_result.json").read_text())
    inputs = {"geometry": GEOMETRY, "cases": CASES, "table": TABLE,
              "curve": CURVE, "producer": HERE / "affine_gate_run.py"}
    assert {name: sha(path) for name, path in inputs.items()} == protocol["sha256"]
    assert sha(HERE / "affine_gate_runtime_info.json") == protocol["sage_runtime_sha256"]
    assert sha(HERE / "affine_gate_protocol.json") == result["protocol_sha256"]
    assert result["status"] == "PASS_N41_FOUR_AXIS_TWO_HALF_AFFINE_GATE"
    assert result["candidate_id"] is None
    assert result["charts"] == 160 and result["families"] == 160*1554
    assert result["source_product_span_rank"] == 7
    assert result["families_retained"] == sum(result["half_survivors"]) == 495
    assert all(sum(hist.values()) == result["families"]
               for hist in result["half_rank_histograms"])
    assert result["source_product_hits"] == [[0,24,37,2,10]]

    spec = importlib.util.spec_from_file_location("n41_curve_audit", CURVE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    curve, elem, integer = module.sage_curve()
    geo = json.loads(GEOMETRY.read_text())
    table = json.loads(TABLE.read_text())
    assert geo["curve_id"] == table["curve_id"] == result["curve_id"]
    witness = [97,151,42,0,14,109,51]
    assert result["witness_state_ids"] == witness
    columns = []
    total = curve(0)
    for axis, sid in enumerate(witness):
        state = geo["blocks"][axis]["states"][sid]
        columns.extend(state["columns"])
        total += curve(*(elem(x) for x in state["raw_sum"]))
    assert len(columns) == len(set(columns)) == result["witness_folded_columns"] == 14
    assert total == curve(*(elem(x) for x in table["raw_target"]))

    # Check the reported inverse hit from input data, without reading any
    # coefficient or selected-root values emitted by the producer.
    cases = [json.loads(line) for line in CASES.read_text().splitlines()]
    row = next(x for x in cases if (x["left_code"],x["right_code"]) == (24,37))
    v = elem(row["reciprocal_coordinates"][2])
    u = v/(v+1)
    t = elem(table["rows"][0][0]["chart"])
    third = geo["blocks"][2]
    s2 = elem(third["s"])**2
    A = t*t+u*(u+1)*t*(t+1)+(t+1)**2
    B = u*(u+1)*t*(t+1)
    D = (u+1)**2*t*t+u*u*(t+1)**2
    c0 = (D+s2*A)**2+s2*B**2
    c1 = B*(D+s2*(A+B))
    c2 = D*(A+B+D)
    product = 0
    for index, raw in enumerate(third["product_basis"]):
        if third["states"][4*10]["a"] >> index & 1:
            product ^= raw
    p = elem(product)
    assert c0+c1*p+c2*p*p == 0
    print(json.dumps({"status":"PASS_N41_AFFINE_GATE_INDEPENDENT_RECEIPT",
                      "witness":witness,"source_product":integer(p),
                      "retained_families":result["families_retained"]},sort_keys=True))


if __name__ == "__main__":
    main()
