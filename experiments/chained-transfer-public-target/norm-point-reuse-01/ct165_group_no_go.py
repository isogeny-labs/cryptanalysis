#!/usr/bin/env python3
"""CT165: odd-primary obstruction to abstract F223-rational point-group transfer.

Scope: any k-isogenous B/k to Weil restriction of CT160 fixed nu12 endpoint.
No quotient construction or ECDLP speedup is certified by this calculation.
"""
import argparse
import copy
import hashlib
import json
from math import gcd, isqrt
from pathlib import Path

FILES = {
    "census": ("CT160_FULL_CENSUS.json", "9a8fb44420385a67eda841e68c4c70c13aedcdb8"),
    "audit": ("CT160_GENERATOR_AUDIT.json", "84086b49178ca298779c771eff1aaeacb3728beb"),
    "kernels": ("CT163_RESULT.json", "1b93b009b1380a6ccbc677ae0d3e6fb7a4decfa9"),
    "quotients": ("CT164_RESULT.json", "e9f7fafedb7b83c21566edfefa6bfcdaf234e6ba"),
}

def require(condition, why):
    if not condition:
        raise ValueError(why)

def pairs_unique(items):
    result = {}
    for k, v in items:
        require(k not in result, "duplicate JSON key")
        result[k] = v
    return result

def bad_constant(x):
    raise ValueError("invalid non-JSON number: " + x)

def read_fixtures(folder):
    objects = {}
    for label, (name, expected_sha) in FILES.items():
        data = (folder / name).read_bytes()
        digest = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        require(digest == expected_sha, f"{name}: changed source blob")
        objects[label] = json.loads(data, object_pairs_hook=pairs_unique, parse_constant=bad_constant)
    return objects

def primality_trial(n):
    if n < 2:
        return False
    for d in range(2, isqrt(n) + 1):
        if n % d == 0:
            return False
    return True

def check(a):
    census, audit, kernels, quotients = (a[k] for k in ("census", "audit", "kernels", "quotients"))
    p, q, n, r = 223, 223 ** 3, 11_086_844, 2_771_711
    require(census.get("schema") == "ct160-fixed-nu12-whole-field-census/v1", "census schema")
    require(type(census.get("field_cardinality")) is int and census["field_cardinality"] == q,
            "wrong cubic field cardinality")
    for k in ("actual_fixed_nu12_source", "actual_fixed_nu12_target"):
        entry = census.get(k)
        require(type(entry) is dict, "missing actual endpoint")
        require(type(entry.get("order")) is int and entry["order"] == n, "endpoint order")
        require(all(type(entry.get(z)) is int for z in ("zeros", "nonzero_squares", "nonsquares")),
                "noninteger census")
        require(entry["zeros"] + entry["nonzero_squares"] + entry["nonsquares"] == q,
                "census population")
        require(2 * entry["nonzero_squares"] + entry["zeros"] + 1 == n,
                "point census recount")
    require(audit.get("field_size") == q and audit.get("cubic_trace") == q + 1 - n,
            "source trace/field mismatch")
    gens = audit.get("model_generators")
    require(type(gens) is list and len(gens) == 2 and
            {v.get("model") for v in gens} == {"fixed_source", "fixed_target"},
            "actual generator identities")
    require(all(type(v.get("generator_prime_order")) is int and
                v["generator_prime_order"] == r and
                type(v.get("group_order")) is int and v["group_order"] == n and
                v.get("on_curve") is True for v in gens), "generator/order assertion")
    require(n == 4 * r and primality_trial(r), "claimed prime-order factor")
    require(kernels.get("assumption", {}).get("p") == p and
            kernels.get("assumption", {}).get("extension_degree") == 3 and
            kernels.get("assumption", {}).get("group_order") == n and
            kernels.get("frobenius_stable_lagrangians") == 9 and
            kernels.get("factorwise") == 3 and kernels.get("mixed") == 6,
            "CT163 fixed source/kernel count mismatch")
    require(quotients.get("schema") == "ct164-even-degree-quotient-two-torsion/v1" and
            quotients.get("field") == p and quotients.get("extension_degree") == 3 and
            quotients.get("full_curve_order") == n and
            quotients.get("rational_2_torsion_size") == 2,
            "CT164 fixed quotient population mismatch")
    kh, qh = kernels.get("kernels"), quotients.get("kernels")
    require(type(kh) is list and type(qh) is list and len(kh) == len(qh) == 9,
            "missing kernel")
    require(len({tuple(v["basis"]) for v in kh}) == 9, "duplicate kernel")
    require([(v["basis"], v["kind"]) for v in kh] ==
            [(v["basis"], v["kind"]) for v in qh], "CT163-CT164 kernel binding")
    require(all(v.get("rational_2_torsion_size_by_m") == [2, 2] for v in qh),
            "CT164 quotient conditions")
    bound = isqrt(4 * p)
    lo, hi = p + 1 - bound, p + 1 + bound
    require((lo, hi) == (195, 253), "Hasse range mismatch")
    rows = [gcd(order, n) for order in range(lo, hi + 1)]
    histogram = {str(g): rows.count(g) for g in sorted(set(rows))}
    require(set(rows) == {1, 2, 4}, "unexpected common factor")
    require(all(v & (v - 1) == 0 for v in rows), "odd shared subgroup")
    return {
        "schema": "ct165-abstract-group-obstruction/v1",
        "base_field": p,
        "actual_fixed_nu12_order": n,
        "odd_prime_factor": r,
        "odd_factor_prime_trial_certified": True,
        "hasse_order_interval": [lo, hi],
        "possible_order_integers_checked": len(rows),
        "gcd_histogram": histogram,
        "maximum_possible_image_order": max(rows),
        "maximum_possible_odd_image_order": 1,
        "fixed_quotient_kernels_bound": len(qh),
        "theorem_scope": "every abstract group hom E(F223)->B(F223), B/F223 F223-isogenous to CT160 Weil restriction",
        "consequence": "no injective scalar-preserving transfer on any odd-prime-order E(F223) subgroup",
        "standing": "[pcc:unverified]; arithmetic source audit, no signed PCC or ECDLP speedup",
    }

def self_test(objects):
    require(check(objects)["maximum_possible_odd_image_order"] == 1, "positive test")
    rejects = []
    for label, change in (
        ("source_order", lambda a: a["census"]["actual_fixed_nu12_source"].__setitem__("order", 11086845)),
        ("census_count", lambda a: a["census"]["actual_fixed_nu12_target"].__setitem__("zeros", 5)),
        ("wrong_generator", lambda a: a["audit"]["model_generators"][0].__setitem__("generator_prime_order", 211)),
        ("wrong_kernels", lambda a: a["kernels"]["kernels"].pop()),
        ("wrong_quotient_order", lambda a: a["quotients"].__setitem__("full_curve_order", 11086842)),
        ("wrong_basis", lambda a: a["quotients"]["kernels"][0].__setitem__("basis", [2, 8, 32])),
        ("counter_as_bool", lambda a: a["audit"]["model_generators"][0].__setitem__("group_order", True)),
    ):
        mutant = copy.deepcopy(objects)
        change(mutant)
        try:
            check(mutant)
        except (ValueError, KeyError, TypeError):
            rejects.append(label)
        else:
            raise ValueError("mutation falsely accepted: " + label)
    return rejects

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    inputs = read_fixtures(args.fixtures)
    result = check(inputs)
    if args.self_test:
        result["negative_controls_rejected"] = self_test(inputs)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))

if __name__ == "__main__":
    main()
