#!/usr/bin/env sage -python
"""Replay the fixed-terminal eliminant on ordinary N41 rows and an N131 block."""

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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def field(n):
    binary = PolynomialRing(GF(2), "t")
    t = binary.gen()
    modulus = t**41 + t**3 + 1 if n == 41 else t**131 + t**13 + t**2 + t + 1
    F = GF(2**n, "t", modulus=modulus)
    return F, EllipticCurve(F, [1, 0, 0, 0, 1]), binary


def decoder(F, binary, n):
    return lambda integer: F(binary([(int(integer) >> bit) & 1 for bit in range(n)]))


def encode(value):
    return sum(int(bit) << index for index, bit in enumerate(value.polynomial().list()))


def polynomial(F, h2, terminal_h2, q, z):
    ring = PolynomialRing(F, "X")
    X = ring.gen()
    k, ell = 1 + h2, 1 + terminal_h2
    assert k and ell
    alpha, beta = X/k, h2/k
    gamma, delta = q/ell, terminal_h2/ell
    A = z*z*alpha*gamma + z
    B = z*z*alpha*delta + alpha
    C = z*z*beta*gamma + gamma
    D = z*z*beta*delta + beta + delta + z*z
    L2 = ell*B*B + q*B*A + terminal_h2*A*A
    L1 = q*(B*C + D*A)
    L0 = ell*D*D + q*D*C + terminal_h2*C*C
    R = L2*alpha + L1
    S = L2*beta + L0
    return k*S*S + X*S*R + h2*R*R


def n41():
    rows = json.loads(INPUTS["n41_rows"].read_text())
    geometry = json.loads(INPUTS["n41_geometry"].read_text())
    fixture = json.loads(INPUTS["n41_fixture"].read_text())
    query = json.loads(INPUTS["n41_query"].read_text())
    assert rows["status"] == "PASS_INDEPENDENT_N41_TERMINAL32_RELATIONS"
    assert len(rows["replayed"]) == 2 and rows["rank_from_empty_matrix"] == 2
    assert query["status"] == "CENSORED_TIME" and len(query["hit_lines"]) == 2
    F, E, binary = field(41)
    dec = decoder(F, binary, 41)
    row_by_mask = {int(row["mask"]): row for row in geometry["rows"]}
    edges = [(mask, mask ^ 184) for mask in sorted(row_by_mask)
             if mask < mask ^ 184 and mask ^ 184 in row_by_mask
             and row_by_mask[mask]["column"] != row_by_mask[mask ^ 184]["column"]]
    assert len(edges) == 35
    w = dec(184 << 1)
    h = sum((w**(2**(2*i)) for i in range(21)), F.zero())
    assert h*h + h == w
    h2 = h*h
    product = lambda masks: dec(masks[0] << 1) * dec(masks[1] << 1)
    cases = []
    for hit_index, hit in enumerate(rows["replayed"]):
        assert hit["status"] == "PASS_INDEPENDENT_RELATION"
        assert hit["raw_target_preimage_index"] == 0
        pairs = hit["source_pairs"]
        assert len(pairs) == 7 and pairs[-1]["edge_id"] < 8
        points = [E(*map(dec, pair["pair_rotated"])) for pair in pairs]
        assert sum(points, E(0)) == E(*map(dec, fixture["raw_target_preimages"][0]))
        first, terminal = points[0], points[-1]
        z = 1 / (first + terminal)[0]
        p = product(pairs[0]["masks"])
        q = product(pairs[-1]["masks"])
        c, d = 1/first[0], 1/terminal[0]
        k = 1 + h2
        assert k*c*c + p*c + h2 == 0
        assert k*d*d + q*d + h2 == 0
        assert (c*d*z)**2 + c*d*z + (c+d+z)**2 == 0
        pool = []
        for terminal_id, masks in enumerate(edges[:8]):
            occupied = {row_by_mask[mask]["column"] for mask in masks}
            source = {encode(product(edge)): edge_id for edge_id, edge in enumerate(edges)
                      if not occupied.intersection(row_by_mask[mask]["column"] for mask in edge)}
            H = polynomial(F, h2, h2, product(masks), z)
            roots = H.roots(multiplicities=False)
            supported = sorted([encode(root), source[encode(root)]]
                               for root in roots if encode(root) in source)
            assert H.degree() == 4 and len(roots) == 4 and len(source) == 34
            pool.append({"terminal_edge": terminal_id, "source_size": len(source),
                         "field_roots": len(roots), "source_hits": supported})
        found = [(item["terminal_edge"], row) for item in pool for row in item["source_hits"]]
        assert found == [(pairs[-1]["edge_id"], [encode(p), pairs[0]["edge_id"]])]
        cases.append({"hit_index": hit_index, "first_edge": pairs[0]["edge_id"],
                      "terminal_edge": pairs[-1]["edge_id"], "first_product": encode(p),
                      "four_point_reciprocal": encode(z), "pool": pool})
    return {"curve_id": rows["curve_id"], "verified_relation_count": 2,
            "novel_rank": 2, "cases": cases}


def n131():
    prior = json.loads(INPUTS["n131_root"].read_text())
    audit = json.loads(INPUTS["n131_audit"].read_text())
    pool = json.loads(INPUTS["n131_pool"].read_text())
    assert prior["status"] == "COMPLETE"
    assert audit["status"] == "PASS_INDEPENDENT_FIXED_TERMINAL_FIELD_SCAN"
    assert prior["source_products"] == audit["source_products"] == 33188
    F, E, binary = field(131)
    dec = decoder(F, binary, 131)
    first = E(*map(dec, prior["first_pair_raw"]))
    terminal = E(*map(dec, prior["terminal_pair_raw"]))
    block = first + terminal
    assert [encode(block[0]), encode(block[1])] == prior["positive_block_point"]
    z = 1/block[0]
    assert encode(z) == prior["cases"]["constructed_positive"]["z"]
    path = INPUTS["n131_pair"]
    spec = importlib.util.spec_from_file_location("pool_root_pair", path)
    pair = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pair)
    columns = {int(a): int(b) for a, b in
               (line.split() for line in INPUTS["n131_support"].read_text().splitlines())}
    codes = list(pair.valid_codes(columns))
    h2 = dec(pair.gf_square(pair.gf_half_trace(pair.coordinate(pair.SEED))))
    terminal_h2 = h2**(2**128)
    seen, rows = set(), []
    for state in pool["states"]:
        code = state["code"]
        if code in seen:
            continue
        seen.add(code)
        occupied = set(state["folded_columns"])
        source = {pair.product_from_code(candidate): candidate for candidate in codes
                  if not occupied.intersection((columns[pair.mask_from_code(candidate)],
                                                 columns[pair.mask_from_code(candidate) ^ pair.SEED]))}
        q = dec(pair.product_from_code(code))**(2**128)
        H = polynomial(F, h2, terminal_h2, q, z)
        roots = H.roots(multiplicities=False)
        supported = sorted([encode(root), source[encode(root)]]
                           for root in roots if encode(root) in source)
        assert H.degree() == 4 and len(roots) == 4
        rows.append({"terminal_code": code, "source_size": len(source),
                     "field_roots": len(roots), "source_hits": supported})
    assert len(rows) == 8
    assert [(row["terminal_code"], hit) for row in rows for hit in row["source_hits"]] == [
        (10, [3328, 4])]
    return {"curve_id": prior["curve_id"], "four_point_reciprocal": encode(z),
            "pool": rows}


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["status"] == "FROZEN_UNPINNED_N41_AND_N131_POOL_ROOT"
    assert protocol["sha256"] == {name: sha(path) for name, path in INPUTS.items()}
    assert protocol["workers"] == 1 and protocol["rss_cap_bytes"] == 4*1024**3
    start = time.monotonic_ns()
    n41_result = n41()
    n131_result = n131()
    elapsed = time.monotonic_ns() - start
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak *= 1024
    assert elapsed < protocol["parent_cap_seconds"] * 10**9
    assert peak < protocol["rss_cap_bytes"]
    result = {"status": "PASS_UNPINNED_N41_AND_N131_POOL_ROOT",
              "candidate_id": None, "protocol_sha256": sha(HERE / "protocol.json"),
              "n41": n41_result, "n131": n131_result,
              "elapsed_ns_exploratory": elapsed, "peak_rss_bytes": peak}
    with (HERE / "result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "n41_cases": len(n41_result["cases"]),
                      "n131_terminal_edges": len(n131_result["pool"]),
                      "elapsed_seconds_exploratory": elapsed/1e9}, sort_keys=True))


if __name__ == "__main__":
    main()
