#!/usr/bin/env python3
"""CT166: exact geometric CM mismatch for actual q223 nu12 elliptic endpoints.

This is a source-only necessary algebraic-homomorphism obstruction.
It does not validate native point counts or prove an ECDLP speedup.
"""
import argparse
import copy
import hashlib
import json
from math import isqrt
from pathlib import Path

CENSUS_BLOB = "9a8fb44420385a67eda841e68c4c70c13aedcdb8"
P = 223
Q = P ** 3
N = 11086844

def require(ok, message):
    if not ok:
        raise ValueError(message)

def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result

def reject_constant(value):
    raise ValueError("nonfinite JSON constant: " + value)

def reject_float(value):
    raise ValueError("noninteger JSON number: " + value)

def read_census(folder):
    raw = (folder / "CT160_FULL_CENSUS.json").read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    require(blob == CENSUS_BLOB, "CT160 census blob changed")
    return json.loads(raw, object_pairs_hook=unique_pairs,
                      parse_constant=reject_constant, parse_float=reject_float)

def prime_factors(n):
    require(type(n) is int and n > 0, "positive integer required")
    factors = []
    d = 2
    while d * d <= n:
        exponent = 0
        while n % d == 0:
            n //= d
            exponent += 1
        if exponent:
            factors.append([d, exponent])
        d += 1 if d == 2 else 2
    if n > 1:
        factors.append([n, 1])
    return factors

def squarefree_part(n):
    require(type(n) is int and n != 0, "nonzero integer required")
    sign = -1 if n < 0 else 1
    product = sign
    for p, exponent in prime_factors(abs(n)):
        if exponent % 2:
            product *= p
    return product

def audit(census):
    require(type(census) is dict, "census object")
    require(census.get("schema") == "ct160-fixed-nu12-whole-field-census/v1", "schema")
    require(type(census.get("field_cardinality")) is int and
            census["field_cardinality"] == Q, "field")
    require(census.get("accepted") is True and census.get("mutant") is False and
            census.get("mutation_rejected") is False, "nominal census flags")
    require(type(census.get("square_roster_cardinality")) is int and
            census["square_roster_cardinality"] == (Q + 1) // 2, "square roster")
    for model in ("actual_fixed_nu12_source", "actual_fixed_nu12_target"):
        row = census.get(model)
        require(type(row) is dict, "missing actual model")
        require(all(type(row.get(k)) is int for k in
                    ("order", "zeros", "nonzero_squares", "nonsquares")), "integer model fields")
        require(row["zeros"] + row["nonzero_squares"] + row["nonsquares"] == Q,
                "model field population")
        require(2 * row["nonzero_squares"] + row["zeros"] + 1 == row["order"] == N,
                "model point count")
    t3 = Q + 1 - N
    disc = t3 * t3 - 4 * Q
    require(t3 == 2724 and t3 % P != 0, "target trace/ordinarity")
    require(disc == -36938092 and disc % 4 == 0, "target discriminant")
    factors = prime_factors(-disc // 4)
    require(factors == [[23, 1], [311, 1], [1291, 1]], "target squarefree factorization")
    cm = squarefree_part(disc)
    require(cm == -9234523, "target CM radicand")
    traces = list(range(-isqrt(4 * P), isqrt(4 * P) + 1))
    require(len(traces) == 59, "Hasse traces")
    ordinary = [t for t in traces if t % P != 0]
    require(len(ordinary) == 58 and 0 in traces, "source ordinary roster")
    radicands = [squarefree_part(t * t - 4 * P) for t in ordinary]
    max_radicand = max(abs(x) for x in radicands)
    require(max_radicand == 883 and max_radicand < abs(cm), "CM collision")
    # Positive control: a genuine cubic base change preserves its ordinary CM field.
    t = 4
    base_change_t3 = t ** 3 - 3 * P * t
    positive = (squarefree_part(base_change_t3 ** 2 - 4 * Q) ==
                squarefree_part(t * t - 4 * P) == -219)
    require(positive, "positive base-change CM control")
    return {
        "schema": "ct166-geometric-cm-obstruction/v1",
        "source_base_field": P,
        "source_extension_field": Q,
        "actual_endpoint_order": N,
        "actual_endpoint_trace": t3,
        "actual_endpoint_discriminant": disc,
        "target_cm_squarefree_radicand": cm,
        "target_cm_factorization": factors,
        "hasse_traces_checked": len(traces),
        "ordinary_source_traces_checked": len(ordinary),
        "supersingular_source_traces": [0],
        "maximum_ordinary_source_cm_radicand_abs": max_radicand,
        "positive_base_change_trace": base_change_t3,
        "positive_base_change_cm_radicand": -219,
        "geometric_algebraic_hom_possible": False,
        "scope": "elliptic source over F223 to actual fixed-nu12 elliptic endpoints or their Weil-restriction F223-isogeny class, after any finite scalar extension",
        "standing": "[pcc:unverified]; source-only integer/CM proof, no independent native ECDLP timing",
    }

def self_test(census):
    mutations = [
        ("source_order", lambda x: x["actual_fixed_nu12_source"].__setitem__("order", N+1)),
        ("target_zeros", lambda x: x["actual_fixed_nu12_target"].__setitem__("zeros", 4)),
        ("boolean_order", lambda x: x["actual_fixed_nu12_source"].__setitem__("order", True)),
        ("wrong_field", lambda x: x.__setitem__("field_cardinality", Q+1)),
        ("missing_model", lambda x: x.pop("actual_fixed_nu12_target")),
    ]
    rejected = []
    for name, mutate in mutations:
        x = copy.deepcopy(census)
        mutate(x)
        try:
            audit(x)
        except (ValueError, TypeError, KeyError):
            rejected.append(name)
        else:
            raise ValueError("mutation falsely accepted: " + name)
    for name, raw in (
        ("duplicate_keys", '{"x":1,"x":2}'),
        ("nan", '{"x":NaN}'),
        ("infinite", '{"x":Infinity}'),
        ("float", '{"x":1.0}'),
    ):
        try:
            json.loads(raw, object_pairs_hook=unique_pairs,
                       parse_constant=reject_constant, parse_float=reject_float)
        except ValueError:
            rejected.append(name)
        else:
            raise ValueError("bad JSON accepted: " + name)
    return rejected

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    census = read_census(args.fixtures)
    result = audit(census)
    if args.self_test:
        result["negative_controls_rejected"] = self_test(census)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))

if __name__ == "__main__":
    main()
