#!/usr/bin/env python3
"""CT171 frozen 48-cohort / CT126 native price-panel coverage guard.
Source-only evidence. It does not price a primitive or solve ECDLP.
Run: python3 -S ct171_selected_coverage.py --self-test
"""
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
import argparse

HERE = Path(__file__).resolve().parent
FIXTURE = HERE.parent / "evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json"
RUST = HERE / "src/main.rs"
FIXTURE_BLOB = "9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3"
RUST_BLOB = "ac4146577f5019fc17674deb342eb5d9fc749715"
SCALARS = (0, 1, 2, 17, 12345, 2771710)
DIRECTIONS = ((0, 2), (2, 0))
ROUTES = {
    "direct_composite": (1, 0, 1),
    "literal_sequential_Jacobian_maps": (0, 2, 2),
    "strongest_retained_lift_chain": (0, 2, 1),
}

def need(ok, message):
    if not ok:
        raise ValueError("CT171 REFUSED: " + message)

def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def strict_json(raw):
    def pairs(items):
        d = {}
        for k, v in items:
            need(k not in d, "duplicate JSON key: " + k)
            d[k] = v
        return d
    def reject_constant(token):
        raise ValueError("non-JSON constant " + token)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=reject_constant)

def typed(v, expected):
    return type(v) is int and v == expected

def check_fixture(f):
    need(type(f) is dict and set(f) == {"all48", "scope"} and
         type(f["scope"]) is str, "top-level schema")
    rows = f["all48"]
    need(type(rows) is list and len(rows) == 48, "exactly 48 selected rows")
    observed = Counter()
    inputs, outputs = set(), set()
    exceptionals, generic = 0, 0
    for i, row in enumerate(rows):
        need(type(row) is dict and
             set(row) == {"from", "to", "sector", "scalar_OUTSIDE_runtime",
                          "input", "whole_outputs_equal", *ROUTES}, "row schema " + str(i))
        a, b, sector, k = (row[n] for n in
                           ("from", "to", "sector", "scalar_OUTSIDE_runtime"))
        need(all(type(z) is int for z in (a, b, sector, k)), "typed cohort " + str(i))
        need((a,b) in DIRECTIONS and sector in range(4) and k in SCALARS,
             "cohort labels " + str(i))
        observed[a,b,sector,k] += 1
        for field, collection in (("input", inputs), ("whole_outputs_equal", outputs)):
            v = row[field]
            need(type(v) is list and len(v) > 0 and
                 all(type(z) is int for z in v), "typed public vector " + field)
            key = (a,b,tuple(v))
            need(key not in collection, "repeated public vector " + field)
            collection.add(key)
        for route, (c169,c13,d) in ROUTES.items():
            cost = row[route]
            need(type(cost) is dict, "route object " + route)
            for label, expected in (("degree169_elliptic_evaluation",c169),
                                    ("degree13_elliptic_evaluation",c13),
                                    ("transported_norm_doubling",d)):
                need(typed(cost.get(label), expected),
                     "route primitive " + route + "/" + label)
        cost = row["strongest_retained_lift_chain"]
        for label in ("explicit_half_check", "generic_ordinate",
                      "generic_halving_factorization", "infinity_halves",
                      "two_torsion_halves"):
            need(type(cost.get(label)) is int, "typed branch counter " + label)
        if k == 0:
            need(cost["explicit_half_check"] == 4 and
                 cost["generic_ordinate"] == 0 and
                 cost["generic_halving_factorization"] == 0 and
                 cost["infinity_halves"] + cost["two_torsion_halves"] == 1,
                 "identity exceptional branch")
            exceptionals += 1
        else:
            need((cost["explicit_half_check"],cost["generic_ordinate"],
                  cost["generic_halving_factorization"],cost["infinity_halves"],
                  cost["two_torsion_halves"]) == (8,4,1,0,0), "generic branch")
            generic += 1
    expected = Counter({(a,b,s,k):1 for a,b in DIRECTIONS
                        for s in range(4) for k in SCALARS})
    need(observed == expected, "2 directions x 4 sectors x 6 scalars grid")
    need((exceptionals,generic) == (8,40), "eight exceptional and 40 generic")
    return {"records":len(rows),"direction_counts":{"0->2":24,"2->0":24},
            "cofactor_sectors_per_direction":4, "scalar_values":list(SCALARS),
            "identity_exceptional":exceptionals, "nonzero_generic":generic,
            "distinct_inputs":len(inputs), "distinct_outputs":len(outputs)}

def check_ct126(source):
    need("let scalars = [1u128, 2, 17, 12_345, ELL as u128 - 1];" in source,
         "CT126 scalar fixture changed")
    need("let source = &runtime.geometry.models[0];" in source and
         "let target = &runtime.geometry.models[2];" in source,
         "CT126 model direction changed")
    need("runtime.transfer_entry(&input, 2)" in source and
         "runtime.retained_lift_entry(&input, 2)" in source,
         "CT126 transfer direction changed")
    need("cofactor_sector" not in source and '"sector"' not in source,
         "CT126 sector metadata changed; re-audit coverage")
    return {"sampled_scalars":[1,2,17,12345,2771710],
            "sampled_direction":"0->2", "samples_identity_case":False,
            "samples_reverse_direction":False, "emits_sector_class":False,
            "eligible_as_full_48_cohort_pricing":False}

def controls(f, source):
    variants = []
    m=copy.deepcopy(f);m["all48"].pop();variants.append(m)
    m=copy.deepcopy(f);m["all48"][0]["sector"]=1;variants.append(m)
    m=copy.deepcopy(f);m["all48"][0]["scalar_OUTSIDE_runtime"]=False;variants.append(m)
    m=copy.deepcopy(f);m["all48"][0]["strongest_retained_lift_chain"]["generic_ordinate"]=4;variants.append(m)
    m=copy.deepcopy(f);m["all48"][0]["strongest_retained_lift_chain"]["transported_norm_doubling"]=2;variants.append(m)
    m=copy.deepcopy(f);m["all48"][1]["input"]=list(m["all48"][0]["input"]);variants.append(m)
    for m in variants:
        try: check_fixture(m)
        except ValueError: continue
        raise ValueError("CT171 ACCEPTED MUTATED REAL FIXTURE")
    for altered in (source.replace("1u128, 2", "0u128, 1, 2"),
                    source.replace("models[0]", "models[2]")):
        try: check_ct126(altered)
        except ValueError: continue
        raise ValueError("CT171 ACCEPTED MUTATED CT126 SOURCE")
    return len(variants)+2

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    fixture_raw=FIXTURE.read_bytes()
    rust_raw=RUST.read_bytes()
    need(blob(fixture_raw)==FIXTURE_BLOB, "original reuse fixture changed")
    need(blob(rust_raw)==RUST_BLOB, "CT126 Rust source changed")
    f=strict_json(fixture_raw)
    source=rust_raw.decode()
    result={"schema":"ct171-coverage/v1", "standing":"[pcc:unverified]",
            "fixture_blob":blob(fixture_raw), "ct126_source_blob":blob(rust_raw),
            "frozen_selected":check_fixture(f), "ct126":check_ct126(source),
            "scope":"source-only coverage gate, no native pricing or ECDLP solve"}
    if args.self_test:
        result["real_fixture_mutations_rejected"]=controls(f,source)
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
