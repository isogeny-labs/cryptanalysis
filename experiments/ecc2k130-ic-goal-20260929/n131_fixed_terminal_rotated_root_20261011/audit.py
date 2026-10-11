"""Independent bit-field scan of the fixed-terminal W18 eliminant."""

import hashlib
import importlib.util
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PAIR = ROOT / "n131_fixed_seed_eight_pair_circuit_20261010/fixed_pair_circuit.py"
GROUP = ROOT / "n131_fixed_seed_halftrace_cubic_20261011/verify.py"
POOL = ROOT / "n131_w18_terminal_fiber_20261011/pool.json"
QUERY = ROOT / "n131_w18_terminal_fiber_20261011/query_result.json"
SUPPORT = ROOT / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def neg(point):
    return (point[0], point[0] ^ point[1])


def main():
    protocol = json.loads((HERE / "audit_protocol.json").read_text())
    inputs = {"source": Path(__file__), "producer": HERE / "result_v2.json",
              "pair": PAIR, "group": GROUP, "pool": POOL,
              "query": QUERY, "support": SUPPORT}
    assert protocol["status"] == "FROZEN_N131_TERMINAL_HALFTRACE_AUDIT"
    assert protocol["sha256"] == {name: sha(path) for name, path in inputs.items()}
    expected = json.loads((HERE / "result_v2.json").read_text())
    pair = load("fixed_terminal_pair_audit", PAIR)
    group = load("fixed_terminal_group_audit", GROUP)
    terminal = json.loads(POOL.read_text())["states"][0]
    query = json.loads(QUERY.read_text())
    columns = {int(a): int(b) for a, b in
               (line.split() for line in SUPPORT.read_text().splitlines())}
    occupied = set(terminal["folded_columns"])
    source_products = {}
    for code in pair.valid_codes(columns):
        a = pair.mask_from_code(code)
        if occupied.intersection((columns[a], columns[a ^ pair.SEED])):
            continue
        p = pair.product_from_code(code)
        assert p not in source_products
        source_products[p] = code
    assert len(source_products) == expected["source_products"] == 33188
    mul, sq = pair.gf_mul, pair.gf_square
    h2 = sq(pair.gf_half_trace(pair.coordinate(pair.SEED)))
    k = 1 ^ h2
    u = pair.gf_frobenius(h2, 128)
    ell = 1 ^ u
    q = pair.gf_frobenius(pair.product_from_code(terminal["code"]), 128)
    ik, ie = group.inverse(k), group.inverse(ell)

    def padd(*items):
        n = max(map(len, items))
        out = [0] * n
        for item in items:
            for i, value in enumerate(item):
                out[i] ^= value
        while len(out) > 1 and out[-1] == 0:
            out.pop()
        return out

    def pmul(left, right):
        out = [0] * (len(left)+len(right)-1)
        for i, a in enumerate(left):
            if a:
                for j, b in enumerate(right):
                    if b:
                        out[i+j] ^= mul(a, b)
        while len(out) > 1 and out[-1] == 0:
            out.pop()
        return out

    def pscale(poly, scalar):
        return [mul(value, scalar) for value in poly]

    def polynomial(z):
        alpha, beta = [0, ik], [mul(h2, ik)]
        gamma, delta = [mul(q, ie)], [mul(u, ie)]
        z2 = sq(z)
        A = padd(pscale(pmul(alpha, gamma), z2), [z])
        B = padd(pscale(pmul(alpha, delta), z2), alpha)
        C = padd(pscale(pmul(beta, gamma), z2), gamma)
        D = padd(pscale(pmul(beta, delta), z2), beta, delta, [z2])
        L2 = padd(pscale(pmul(B, B), ell), pscale(pmul(B, A), q),
                  pscale(pmul(A, A), u))
        L1 = pscale(padd(pmul(B, C), pmul(D, A)), q)
        L0 = padd(pscale(pmul(D, D), ell), pscale(pmul(D, C), q),
                  pscale(pmul(C, C), u))
        R = padd(pmul(L2, alpha), L1)
        S = padd(pmul(L2, beta), L0)
        return padd(pscale(pmul(S, S), k),
                    pmul([0, 1], pmul(S, R)),
                    pscale(pmul(R, R), h2))

    def evaluate(poly, x):
        value = 0
        for coefficient in reversed(poly):
            value = mul(value, x) ^ coefficient
        return value

    first = group.point_add(group.point_options(4)[0], group.point_options(208)[0])
    last = tuple(terminal["rotated_raw_point"])
    block = group.point_add(first, last)
    assert block is not None and list(block) == expected["positive_block_point"]
    assert group.point_add(tuple(query["residuals"][0]["point"]), last) == tuple(query["raw_target"])
    c, d = group.inverse(first[0]), group.inverse(last[0])
    p0 = pair.product_from_code(pair.selector_code(4))
    assert mul(k, sq(c)) ^ mul(p0, c) ^ h2 == 0
    assert mul(ell, sq(d)) ^ mul(q, d) ^ u == 0
    positive_z = group.inverse(block[0])
    assert sq(mul(mul(c, d), positive_z)) ^ mul(mul(c, d), positive_z) ^ sq(c ^ d ^ positive_z) == 0
    assert positive_z == expected["cases"]["constructed_positive"]["z"]
    rows = {}
    for name, item in expected["cases"].items():
        start = time.monotonic_ns()
        poly = polynomial(item["z"])
        assert len(poly)-1 == item["degree"] == 4
        actual = sorted((p, code) for p, code in source_products.items()
                        if evaluate(poly, p) == 0)
        assert actual == [tuple(v) for v in item["source_supported_products_and_codes"]]
        assert all(evaluate(poly, root) == 0 for root in item["field_roots"])
        rows[name] = {"source_hits": actual, "scan_ns": time.monotonic_ns()-start,
                      "source_products_checked": len(source_products)}
        assert rows[name]["scan_ns"] < protocol["cap_seconds_per_case"]*10**9
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak *= 1024
    out = {"status": "PASS_INDEPENDENT_FIXED_TERMINAL_FIELD_SCAN",
           "curve_id": expected["curve_id"], "positive_product": p0,
           "terminal_product_rotated": q, "source_products": len(source_products),
           "cases": rows, "peak_rss_bytes": peak,
           "protocol_sha256": sha(HERE / "audit_protocol.json")}
    assert peak < protocol["rss_cap_bytes"]
    (HERE / "audit.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"status": out["status"], "cases": {
        name: {"hits": len(row["source_hits"]), "seconds": row["scan_ns"]/1e9}
        for name, row in rows.items()}}))


if __name__ == "__main__":
    main()
