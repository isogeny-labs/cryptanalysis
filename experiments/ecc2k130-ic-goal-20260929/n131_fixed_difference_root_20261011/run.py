#!/usr/bin/env sage -python
"""Root extraction from the same-seed four-atom eliminant at fixed product difference."""

import hashlib
import json
import resource
import sys
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "n131_w14_coupled_fouratom_inverse_20261010"
TERMS = ROOT / "resultant_terms.json"
INPUTS = ROOT / "inputs.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def field(panel):
    B = PolynomialRing(GF(2), "t")
    t = B.gen()
    return GF(2**panel["field_degree"], "t", modulus=sum(t**i for i in panel["field_modulus_exponents"]))


def decode(F, value):
    result, power = F.zero(), F.one()
    while value:
        if value & 1:
            result += power
        value >>= 1
        power *= F.gen()
    return result


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial()))


def product_image(F, dimension, seed):
    values = [F.zero()]
    for i in range(1, dimension + 1):
        w = F.gen()**i
        v = w*w + seed*w
        if v and v not in values:
            values += [p+v for p in values]
    assert len(values) == 2**(dimension-1)
    return values


def polynomial_at_difference(F, terms, seed, delta, z):
    R = PolynomialRing(F, "X")
    X = R.gen()
    xpow = [X**i for i in range(9)]
    ypow = [(X+delta)**i for i in range(9)]
    spow = [seed**i for i in range(17)]
    zpow = [z**i for i in range(9)]
    H = R.zero()
    for s, p, q, t in terms:
        H += spow[s]*zpow[t]*xpow[p]*ypow[q]
    return H


def direct_value(terms, s, p, q, z):
    acc = s.parent().zero()
    sp = [s**i for i in range(17)]
    pp = [p**i for i in range(9)]
    qp = [q**i for i in range(9)]
    zp = [z**i for i in range(9)]
    for a, b, c, d in terms:
        acc += sp[a]*pp[b]*qp[c]*zp[d]
    return acc


def main():
    p = json.loads((HERE / "protocol.json").read_text())
    assert p["status"] == "FROZEN_FIXED_DIFFERENCE_ROOT_GATE"
    assert p["sha256"] == {"source": sha(Path(__file__)), "terms": sha(TERMS),
                           "inputs": sha(INPUTS), "runtime": sha(HERE / "sage_runtime_info.json")}
    terms = [tuple(row) for row in json.loads(TERMS.read_text())["terms_s_p_q_z"]]
    inputs = json.loads(INPUTS.read_text())["panels"]
    result = {"status": "COMPLETE", "candidate_id": None, "panels": {},
              "protocol_sha256": sha(HERE / "protocol.json"),
              "source_sha256": sha(Path(__file__))}
    for label in ("41", "131"):
        panel = inputs[label]
        F = field(panel)
        seed = decode(F, panel["source_sum_field"])
        p0, q0 = [decode(F, value) for value in panel["pair_products"]]
        delta = p0+q0
        assert delta != 0
        setup_start = time.monotonic_ns()
        image = product_image(F, panel["source_dimension"], seed)
        image_set = set(image)
        assert p0 in image_set and q0 in image_set
        setup_ns = time.monotonic_ns()-setup_start
        rows = {}
        for name, value in (("positive", panel["positive_z"]),
                            ("trace_zero_control", panel["trace_zero_control_z"])):
            z = decode(F, value)
            query_start = time.monotonic_ns()
            H = polynomial_at_difference(F, terms, seed, delta, z)
            roots = H.roots(multiplicities=False)
            root_ns = time.monotonic_ns()-query_start
            supported = {r for r in roots if r in image_set}
            scan_start = time.monotonic_ns()
            scanned = {v for v in image if H(v) == 0}
            scan_ns = time.monotonic_ns()-scan_start
            assert supported == scanned
            assert all(direct_value(terms, seed, r, r+delta, z) == 0 for r in roots)
            assert H(p0) == 0 if name == "positive" else True
            rows[name] = {"z": value, "degree": int(H.degree()),
                          "coefficient_count": sum(bool(c) for c in H.list()),
                          "all_field_roots": sorted(encode(r) for r in roots),
                          "source_supported_roots": sorted(encode(r) for r in supported),
                          "root_query_ns": root_ns, "full_image_scan_ns": scan_ns,
                          "source_products_checked_by_scan": len(image)}
            assert root_ns < p["cap_seconds_per_case"]*10**9
            assert scan_ns < p["cap_seconds_per_case"]*10**9
        if label == "131":
            E = EllipticCurve(F, [1, 0, 0, 0, 1])
            atoms = [E(decode(F, x), decode(F, y)) for x, y in panel["raw_diagonal_atoms"]]
            raw = sum(atoms, E(0))
            assert [encode(raw[0]), encode(raw[1])] == panel["raw_four_atom_sum"]
            assert encode(raw[0]**(-1)) == panel["positive_z"]
        result["panels"][label] = {"curve_id": panel["curve_id"],
                                   "seed": panel["source_sum_field"],
                                   "product_difference": encode(delta),
                                   "source_product_image_size": len(image),
                                   "setup_ns": setup_ns, "cases": rows}
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak *= 1024
    result["peak_rss_bytes"] = peak
    assert peak < p["rss_cap_bytes"]
    (HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"status": result["status"], "panels": {
        key: {name: {"degree": row["degree"], "supported": len(row["source_supported_roots"]),
                     "root_seconds": row["root_query_ns"]/1e9,
                     "scan_seconds": row["full_image_scan_ns"]/1e9}
              for name, row in value["cases"].items()}
        for key, value in result["panels"].items()}}))


if __name__ == "__main__":
    main()
