"""Independent bit-field scan of every N131 terminal-edge product polynomial."""

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
SUPPORT = ROOT / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
POOL = ROOT / "n131_w18_terminal_fiber_20261011/pool.json"
ROOT_AUDIT = ROOT / "n131_fixed_terminal_rotated_root_20261011/audit.json"
INPUTS = {"source": HERE / "audit.py", "producer": HERE / "result.json",
          "pair": PAIR, "support": SUPPORT, "pool": POOL,
          "root_audit": ROOT_AUDIT}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    protocol = json.loads((HERE / "audit_protocol.json").read_text())
    assert protocol["status"] == "FROZEN_POOL_BITFIELD_AUDIT"
    assert protocol["sha256"] == {name: sha(path) for name, path in INPUTS.items()}
    producer = json.loads((HERE / "result.json").read_text())
    assert producer["status"] == "PASS_UNPINNED_N41_AND_N131_POOL_ROOT"
    prior = json.loads(ROOT_AUDIT.read_text())
    assert prior["status"] == "PASS_INDEPENDENT_FIXED_TERMINAL_FIELD_SCAN"
    assert prior["positive_product"] == 3328
    pair = load("pool_audit_pair", PAIR)
    pool = json.loads(POOL.read_text())
    columns = {int(a): int(b) for a, b in
               (line.split() for line in SUPPORT.read_text().splitlines())}
    codes = list(pair.valid_codes(columns))
    mul, sq, rot = pair.gf_mul, pair.gf_square, pair.gf_frobenius

    def inverse(value):
        assert value
        exponent, result = (1 << 131) - 2, 1
        while exponent:
            if exponent & 1:
                result = mul(result, value)
            value = sq(value)
            exponent >>= 1
        return result

    def add(*terms):
        out = [0] * max(map(len, terms))
        for term in terms:
            for index, value in enumerate(term):
                out[index] ^= value
        while len(out) > 1 and out[-1] == 0:
            out.pop()
        return out

    def product(left, right):
        out = [0] * (len(left) + len(right) - 1)
        for i, a in enumerate(left):
            if a:
                for j, b in enumerate(right):
                    if b:
                        out[i+j] ^= mul(a, b)
        while len(out) > 1 and out[-1] == 0:
            out.pop()
        return out

    def scale(poly, scalar):
        return [mul(value, scalar) for value in poly]

    def evaluate(poly, x):
        value = 0
        for coefficient in reversed(poly):
            value = mul(value, x) ^ coefficient
        return value

    h2 = sq(pair.gf_half_trace(pair.coordinate(pair.SEED)))
    k = 1 ^ h2
    terminal_h2 = rot(h2, 128)
    ell = 1 ^ terminal_h2
    ik, ie = inverse(k), inverse(ell)
    z = producer["n131"]["four_point_reciprocal"]
    z2 = sq(z)
    seen, results = set(), []
    for state in pool["states"]:
        code = state["code"]
        if code in seen:
            continue
        seen.add(code)
        start = time.monotonic_ns()
        occupied = set(state["folded_columns"])
        source = {pair.product_from_code(candidate): candidate for candidate in codes
                  if not occupied.intersection((columns[pair.mask_from_code(candidate)],
                                                 columns[pair.mask_from_code(candidate) ^ pair.SEED]))}
        q = rot(pair.product_from_code(code), 128)
        alpha, beta = [0, ik], [mul(h2, ik)]
        gamma, delta = [mul(q, ie)], [mul(terminal_h2, ie)]
        A = add(scale(product(alpha, gamma), z2), [z])
        B = add(scale(product(alpha, delta), z2), alpha)
        C = add(scale(product(beta, gamma), z2), gamma)
        D = add(scale(product(beta, delta), z2), beta, delta, [z2])
        L2 = add(scale(product(B, B), ell), scale(product(B, A), q),
                 scale(product(A, A), terminal_h2))
        L1 = scale(add(product(B, C), product(D, A)), q)
        L0 = add(scale(product(D, D), ell), scale(product(D, C), q),
                 scale(product(C, C), terminal_h2))
        R = add(product(L2, alpha), L1)
        S = add(product(L2, beta), L0)
        H = add(scale(product(S, S), k), product([0, 1], product(S, R)),
                scale(product(R, R), h2))
        assert len(H) == 5
        hits = sorted([value, candidate] for value, candidate in source.items()
                      if evaluate(H, value) == 0)
        expected = next(row for row in producer["n131"]["pool"]
                        if row["terminal_code"] == code)
        assert hits == expected["source_hits"]
        elapsed = time.monotonic_ns() - start
        assert elapsed < protocol["cap_seconds_per_edge"] * 10**9
        results.append({"terminal_code": code, "source_size": len(source),
                        "polynomial_degree": len(H)-1, "source_hits": hits,
                        "scan_ns": elapsed})
    assert len(results) == 8
    assert [(row["terminal_code"], hit) for row in results for hit in row["source_hits"]] == [
        (10, [3328, 4])]
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak *= 1024
    assert peak < protocol["rss_cap_bytes"]
    output = {"status": "PASS_INDEPENDENT_EIGHT_EDGE_BITFIELD_SCAN",
              "curve_id": producer["n131"]["curve_id"],
              "protocol_sha256": sha(HERE / "audit_protocol.json"),
              "rows": results, "peak_rss_bytes": peak}
    with (HERE / "audit_result.json").open("x") as stream:
        json.dump(output, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": output["status"], "edges": len(results),
                      "products_checked": sum(row["source_size"] for row in results),
                      "hits": sum(len(row["source_hits"]) for row in results)}, sort_keys=True))


if __name__ == "__main__":
    main()
