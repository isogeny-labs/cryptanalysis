#!/usr/bin/env python3
"""CT162: mod-2 hyperelliptic genus-3 carrier + odd-isogeny 2-torsion screen.

Source-only necessary conditions, NOT a construction or solve. [pcc:unverified]
Uses only Python stdlib; CT160 census is a frozen input by SHA-256.
"""
import argparse
import hashlib
import json
from pathlib import Path

CENSUS_SHA256 = "58af5c02d3a5afc722e1662e2fb5ade0534e65f824a29c97abc51dab827d08c8"
P = 223
Q = P ** 3
EXPECTED_ORDER = 11_086_844


def require(test, why):
    if not test:
        raise ValueError(why)


def unique_keys(pairs):
    result = {}
    for k, v in pairs:
        require(k not in result, "duplicate JSON key")
        result[k] = v
    return result


def finite_constant(s):
    raise ValueError("invalid nonfinite constant: " + s)


def reject_float(s):
    raise ValueError("floating-point number not admitted in census: " + s)


def parse_json(raw):
    return json.loads(raw, object_pairs_hook=unique_keys, parse_constant=finite_constant, parse_float=reject_float)


def verify_census(obj):
    require(type(obj) is dict and set(obj) == {
        "schema", "field_cardinality", "square_roster_cardinality",
        "actual_fixed_nu12_source", "actual_fixed_nu12_target",
        "independent_explicit_original_twist_control", "mutant", "accepted", "mutation_rejected"
    }, "wrong census schema")
    require(obj["schema"] == "ct160-fixed-nu12-whole-field-census/v1", "wrong CT160 schema")
    require(type(obj["field_cardinality"]) is int and obj["field_cardinality"] == Q, "wrong field")
    require(type(obj["square_roster_cardinality"]) is int and obj["square_roster_cardinality"] == (Q+1)//2, "wrong square roster")
    require(obj["accepted"] is True and obj["mutant"] is False and obj["mutation_rejected"] is False, "mutant or unaccepted")
    for name in ("actual_fixed_nu12_source", "actual_fixed_nu12_target"):
        d = obj[name]
        require(type(d) is dict and set(d) == {"zeros", "nonzero_squares", "nonsquares", "order"}, "curve-count schema")
        for key in d:
            require(type(d[key]) is int and d[key] >= 0, "non-integer census datum")
        require(d["zeros"] == 3, "wrong rational 2-torsion root count")
        require(d["zeros"]+d["nonzero_squares"]+d["nonsquares"] == Q, "not all field values classified")
        require(1+d["zeros"]+2*d["nonzero_squares"] == d["order"] == EXPECTED_ORDER, "wrong elliptic order")
        require(d["nonzero_squares"] == 5_543_420, "wrong square population")
    return Q+1-EXPECTED_ORDER


def partitions(n, min_part=1):
    if not n:
        yield ()
    for d in range(min_part, n+1):
        for tail in partitions(n-d, d):
            yield (d,) + tail


def gf2_multiply(a, b):
    out = 0
    while b:
        if b & 1:
            out ^= a
        a <<= 1
        b >>= 1
    return out


def gf2_exact_divide(a, b):
    require(b, "zero polynomial divisor")
    out = 0
    while a and a.bit_length() >= b.bit_length():
        shift = a.bit_length()-b.bit_length()
        out ^= 1 << shift
        a ^= b << shift
    require(a == 0, "nonexact GF2 quotient")
    return out


def permutation(parts):
    require(all(type(d) is int and d > 0 for d in parts) and sum(parts) == 8, "bad orbit partition")
    result = list(range(8))
    start = 0
    for d in parts:
        for i in range(d):
            result[start+i] = start + ((i+1) % d)
        start += d
    require(sorted(result) == list(range(8)), "not a permutation")
    return result


def permute(mask, action):
    out = 0
    for bit, target in enumerate(action):
        if mask & (1 << bit):
            out ^= 1 << target
    return out


def weierstrass_charpoly_mod2(parts):
    require(sum(parts) == 8, "wrong polynomial orbit degree")
    numerator = 1
    for d in parts:
        numerator = gf2_multiply(numerator, (1 << d) ^ 1)
    return gf2_exact_divide(numerator, 0b101)  # (X+1)^2 over F2


def rational_two_torsion_count(parts):
    action = permutation(parts)
    # Even subsets modulo complement: pick exactly one rep from each pair.
    reps = [mask for mask in range(256) if mask.bit_count() % 2 == 0 and (mask & 128) == 0]
    require(len(reps) == 64, "incorrect J[2] dimension")
    total = 0
    for mask in reps:
        image = permute(mask, action)
        total += (image == mask or image == (mask ^ 255))
    require(total > 0 and total & (total-1) == 0, "invalid rational 2-torsion rank")
    return total


def classify(trace, order_2):
    require(type(trace) is int and type(order_2) is int, "incorrect types")
    # In genus 3, for odd characteristic, the Weil polynomial is
    # X^6 - trace X^3 + p^3. Modulo 2 its bit-polynomial is exactly:
    f2 = (1 << 6) ^ ((trace & 1) << 3) ^ (Q & 1)
    all_parts = list(partitions(8))
    require(len(all_parts) == 22 and len(set(all_parts)) == 22, "partition enumeration incomplete")
    accepted = []
    for p in all_parts:
        if weierstrass_charpoly_mod2(p) == f2:
            fixed = rational_two_torsion_count(p)
            accepted.append({"partition": list(p), "rational_J2_count": fixed,
                             "compatible_if_odd_degree_isogeny": fixed == order_2})
    return {"weil_polynomial_mod2_bitset": f2, "total_partitions": len(all_parts),
            "mod2_admissible": accepted, "odd_degree_compatible": [x["partition"] for x in accepted if x["compatible_if_odd_degree_isogeny"]]}


def check_mutants(census):
    import copy
    count = 0
    attempts = []
    a = copy.deepcopy(census)
    a["field_cardinality"] += 1
    attempts.append((lambda obj=a: verify_census(obj), "field"))
    a = copy.deepcopy(census)
    a["actual_fixed_nu12_source"]["zeros"] = 2
    attempts.append((lambda obj=a: verify_census(obj), "two_torsion"))
    a = copy.deepcopy(census)
    a["actual_fixed_nu12_target"]["order"] = True
    attempts.append((lambda obj=a: verify_census(obj), "boolean_count"))
    attempts.append((lambda: parse_json('{"x":1,"x":2}'), "duplicate_key"))
    attempts.append((lambda: parse_json('{"x":NaN}'), "nonfinite_constant"))
    attempts.append((lambda: parse_json('{"x":1e999}'), "nonfinite_exponent"))
    attempts.append((lambda: permutation((1, 1, 3, 2)), "invalid_partition"))
    attempts.append((lambda: require(weierstrass_charpoly_mod2((1, 1, 1, 1, 1, 1, 1, 1)) == 0x41, "incorrect polynomial partition"), "mismatched_polynomial"))
    attempts.append((lambda: require(classify(2725, 4)["weil_polynomial_mod2_bitset"] == 0x41, "wrong trace parity"), "trace_mutant"))
    for fn, label in attempts:
        try:
            fn()
        except (ValueError, AssertionError):
            count += 1
        else:
            raise ValueError("mutation wrongly accepted: " + label)
    return count


def run(path, self_test):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == CENSUS_SHA256, "frozen CT160 SHA-256 mismatch")
    census = parse_json(raw)
    trace = verify_census(census)
    require(trace == 2724, "not CT160 cubic trace")
    result = classify(trace, 4)
    require(result["weil_polynomial_mod2_bitset"] == 0x41, "wrong Weil polynomial")
    require(len(result["mod2_admissible"]) == 4, "unexpected genus-3 screen count")
    require(len(result["odd_degree_compatible"]) == 2, "unexpected odd-degree screen count")
    return {"schema": "ct162-genus3-weierstrass-torsion/v1", "status": "[pcc:unverified]",
            "census_sha256": CENSUS_SHA256, "field": P, "extension_degree": 3,
            "cubic_trace": trace, "weil_polynomial": [Q, 0, 0, -trace, 0, 0, 1],
            "source_and_target_rational_2_torsion_points": 4,
            "hypothesis": "hyperelliptic genus-3 Jacobian F223-isogenous to fixed-nu12 Weil restriction",
            "conditional_odd_degree_2_torsion_filter": True,
            **result, "mutations_rejected": check_mutants(census) if self_test else None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--census", type=Path, default=Path(__file__).with_name("CT160_FULL_CENSUS.json"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.census,args.self_test), sort_keys=True,separators=(',',':')))


if __name__ == "__main__":
    main()
