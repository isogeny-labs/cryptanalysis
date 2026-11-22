#!/usr/bin/env sage -python
"""Degree-eight symmetric quotient and Artin-Schreier recovery of product roots."""

import hashlib
import json
import resource
import sys
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "n131_w14_coupled_fouratom_inverse_20261010"
TERMS = ROOT / "resultant_terms.json"
INPUTS = ROOT / "inputs.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def field(panel):
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    return GF(2**panel["field_degree"], "t", modulus=sum(t**i for i in panel["field_modulus_exponents"]))


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


def quotient_terms(terms):
    # p^k+q^k expressed in P=p+q and T=pq.
    powers = [set(), {(1, 0)}]
    for _ in range(2, 9):
        powers.append({(a+1, b) for a, b in powers[-1]}
                      ^ {(a, b+1) for a, b in powers[-2]})
    output, visited = set(), set()
    for s, p, q, z in sorted(terms):
        if (s, p, q, z) in visited:
            continue
        assert (s, q, p, z) in terms
        if p == q:
            orbit = {(s, 0, p, z)}
        else:
            orbit = {(s, a, b+min(p, q), z) for a, b in powers[abs(p-q)]}
        output ^= orbit
        visited.update(((s, p, q, z), (s, q, p, z)))
    assert visited == terms and len(output) == 87
    return output


def half_trace(value, n):
    result, power = value.parent().zero(), value
    for _ in range((n-1)//2+1):
        result += power
        power = power**4
    return result


def main():
    protocol = json.loads((HERE / "quotient_protocol.json").read_text())
    assert protocol["status"] == "FROZEN_FIXED_DIFFERENCE_QUOTIENT"
    assert protocol["sha256"] == {"source": sha(Path(__file__)),
                                   "terms": sha(TERMS), "inputs": sha(INPUTS),
                                   "prior": sha(HERE / "result.json"),
                                   "runtime": sha(HERE / "sage_runtime_info.json")}
    original = {tuple(row) for row in json.loads(TERMS.read_text())["terms_s_p_q_z"]}
    quotient = quotient_terms(original)
    prior = json.loads((HERE / "result.json").read_text())
    inputs = json.loads(INPUTS.read_text())["panels"]
    out = {"status": "COMPLETE", "candidate_id": None, "quotient_terms": len(quotient),
           "panels": {}, "protocol_sha256": sha(HERE / "quotient_protocol.json")}
    for label in ("41", "131"):
        panel, earlier = inputs[label], prior["panels"][label]
        F = field(panel)
        s = decode(F, panel["source_sum_field"])
        delta = decode(F, earlier["product_difference"])
        assert delta != 0
        R = PolynomialRing(F, "T")
        T = R.gen()
        cases = {}
        for name, record in earlier["cases"].items():
            z = decode(F, record["z"])
            start = time.monotonic_ns()
            J = sum((s**a * delta**b * T**c * z**d
                     for a, b, c, d in quotient), R.zero())
            roots_T = J.roots(multiplicities=False)
            recovered = set()
            for value in roots_T:
                normalized = value/(delta*delta)
                if normalized.trace() != 0:
                    continue
                u = half_trace(normalized, panel["field_degree"])
                assert u*u+u == normalized
                recovered.update((delta*u, delta*(u+1)))
            elapsed = time.monotonic_ns()-start
            encoded = sorted(encode(r) for r in recovered)
            assert encoded == record["all_field_roots"]
            assert elapsed < protocol["cap_seconds_per_case"]*10**9
            cases[name] = {"quotient_degree": int(J.degree()),
                           "quotient_coefficient_count": sum(bool(c) for c in J.list()),
                           "quotient_field_roots": sorted(encode(r) for r in roots_T),
                           "recovered_product_roots": encoded,
                           "query_ns": elapsed}
        out["panels"][label] = {"curve_id": panel["curve_id"], "cases": cases}
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak *= 1024
    out["peak_rss_bytes"] = peak
    assert peak < protocol["rss_cap_bytes"]
    (HERE / "quotient_result.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"status": out["status"], "panels": {
        label: {name: {"degree": case["quotient_degree"],
                       "roots": len(case["recovered_product_roots"]),
                       "seconds": case["query_ns"]/1e9}
                for name, case in row["cases"].items()}
        for label, row in out["panels"].items()}}))


if __name__ == "__main__":
    main()
