#!/usr/bin/env sage -python
"""Degree-eight rotated resultant with one terminal pair product fixed."""

import hashlib
import importlib.util
import json
import resource
import sys
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULTANT = ROOT / "n131_w15_rotated_fouratom_inverse_20261010/resultant.json"
FIXTURE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011/control_fixture.json"
POOL = ROOT / "n131_w18_terminal_fiber_20261011/pool.json"
QUERY = ROOT / "n131_w18_terminal_fiber_20261011/query_result.json"
SUPPORT = ROOT / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
PAIR = ROOT / "n131_fixed_seed_eight_pair_circuit_20261010/fixed_pair_circuit.py"
GROUP = ROOT / "n131_fixed_seed_halftrace_cubic_20261011/verify.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def decode(F, integer):
    value, power = F.zero(), F.one()
    while integer:
        if integer & 1:
            value += power
        integer >>= 1
        power *= F.gen()
    return value


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial()))


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    inputs = {"source": Path(__file__), "resultant": RESULTANT,
              "fixture": FIXTURE, "pool": POOL, "query": QUERY,
              "support": SUPPORT, "pair": PAIR, "group": GROUP,
              "runtime": HERE / "sage_runtime_info.json"}
    assert protocol["status"] == "FROZEN_N131_FIXED_TERMINAL_ROTATED_ROOT"
    assert protocol["sha256"] == {name: sha(path) for name, path in inputs.items()}
    terms_record = json.loads(RESULTANT.read_text())
    assert terms_record["variable_order"] == ["a", "b", "p", "q", "z"]
    terms = terms_record["terms"]
    fixture = json.loads(FIXTURE.read_text())
    pool = json.loads(POOL.read_text())
    query = json.loads(QUERY.read_text())
    pair = load("rotated_root_pair", PAIR)
    group = load("rotated_root_group", GROUP)
    terminal = pool["states"][0]
    assert terminal["code"] == fixture["selected"][8]["masks"][0] == 10
    assert terminal["signs"] == [0, 0] and terminal["masks"] == [10, 222]
    source = fixture["selected"][0]
    assert source["rotation"] == 0 and source["masks"] == [4, 208]
    assert source["product_p"] == pair.product_from_code(
        pair.selector_code(source["masks"][0]))
    assert fixture["selected"][8]["product_p"] == pair.product_from_code(terminal["code"])
    B = PolynomialRing(GF(2), "t")
    t = B.gen()
    F = GF(2**131, "t", modulus=t**131+t**13+t**2+t+1)
    E = EllipticCurve(F, [1, 0, 0, 0, 1])
    def point(raw):
        return E(decode(F, raw[0]), decode(F, raw[1]))
    first_raw = group.point_add(group.point_options(4)[0],
                                group.point_options(208)[0])
    assert first_raw is not None
    first = point(first_raw)
    last = point(terminal["rotated_raw_point"])
    block = first+last
    assert block != E(0) and encode(block[0]) not in (0, 1)
    positive_z = encode(block[0]**(-1))
    raw_public_residual = query["residuals"][0]["point"]
    public_residual = point(raw_public_residual)
    assert public_residual+last == point(query["raw_target"])
    public_z = encode(public_residual[0]**(-1))
    assert public_z == query["residuals"][0]["standard_reciprocal"]
    seed = decode(F, pair.coordinate(pair.SEED))
    a = seed
    b = seed**(2**128)
    q = decode(F, pair.product_from_code(terminal["code"]))**(2**128)
    expected_p = pair.product_from_code(pair.selector_code(4))
    columns = {int(x): int(y) for x, y in
               (line.split() for line in SUPPORT.read_text().splitlines())}
    occupied = set(terminal["folded_columns"])
    codes = [c for c in pair.valid_codes(columns)
             if not occupied.intersection(
                 (columns[pair.mask_from_code(c)],
                  columns[pair.mask_from_code(c)^pair.SEED]))]
    products = {pair.product_from_code(c): c for c in codes}
    assert len(products) == len(codes) == 33188
    assert expected_p in products
    setup_end = time.monotonic_ns()
    R = PolynomialRing(F, "X")
    X = R.gen()
    rows = {}
    for name, value in (("constructed_positive", positive_z),
                        ("field_control", 3),
                        ("frozen_public_residual", public_z)):
        z = decode(F, value)
        start = time.monotonic_ns()
        ap = [a**i for i in range(9)]
        bp = [b**i for i in range(9)]
        qp = [q**i for i in range(9)]
        zp = [z**i for i in range(9)]
        xp = [X**i for i in range(9)]
        H = sum((ap[i]*bp[j]*xp[k]*qp[l]*zp[m]
                 for i, j, k, l, m in terms), R.zero())
        roots = H.roots(multiplicities=False)
        elapsed = time.monotonic_ns()-start
        supported = sorted((encode(root), products[encode(root)])
                           for root in roots if encode(root) in products)
        # The dictionary is keyed by integer polynomial encodings.
        rows[name] = {"z": value, "degree": int(H.degree()),
                      "field_roots": sorted(encode(root) for root in roots),
                      "source_supported_products_and_codes": supported,
                      "query_ns": elapsed}
        assert elapsed < protocol["cap_seconds_per_case"]*10**9
    assert any(p == expected_p for p, _ in
               rows["constructed_positive"]["source_supported_products_and_codes"])
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak *= 1024
    out = {"status": "COMPLETE", "candidate_id": None,
           "curve_id": protocol["curve_id"], "terminal_code": terminal["code"],
           "terminal_product_unrotated": pair.product_from_code(terminal["code"]),
           "first_product_positive": expected_p,
           "first_pair_raw": list(first_raw),
           "terminal_pair_raw": terminal["rotated_raw_point"],
           "positive_block_point": [encode(block[0]), encode(block[1])],
           "source_products": len(products), "cases": rows,
           "setup_end_ns": setup_end, "peak_rss_bytes": peak,
           "protocol_sha256": sha(HERE / "protocol.json"),
           "source_sha256": sha(Path(__file__))}
    assert peak < protocol["rss_cap_bytes"]
    (HERE / "result.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"status": out["status"], "cases": {
        name: {"degree": row["degree"],
               "supported": len(row["source_supported_products_and_codes"]),
               "seconds": row["query_ns"]/1e9}
        for name, row in rows.items()}}))


if __name__ == "__main__":
    main()
