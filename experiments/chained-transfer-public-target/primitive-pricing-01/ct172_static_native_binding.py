#!/usr/bin/env python3
"""CT172 source-only binding: the *actual* CT125 Rust Calls layout versus 48 real rows.

No Rust code is compiled or run; this is not an independent arithmetic replay.
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "fixed-jacobian-chain-evaluator-02/derived/lib.rs"
FIXTURE = ROOT / "evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json"
SRC_BLOB = "b80eb91a39ae1e87f0fcde95e52ea3d3634558bc"
FIX_BLOB = "9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3"
ROUTES = ("direct_composite", "literal_sequential_Jacobian_maps",
          "strongest_retained_lift_chain")


def need(ok, label):
    if not ok:
        raise ValueError("CT172 refused: " + label)


def git_blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def strict_json(raw):
    def object_pairs(pairs):
        out = {}
        for key, value in pairs:
            need(key not in out, "duplicate JSON key " + key)
            out[key] = value
        return out

    def reject_constant(name):
        raise ValueError("non-JSON number " + name)

    return json.loads(raw, object_pairs_hook=object_pairs,
                      parse_constant=reject_constant)


def rust_fields(source):
    match = re.search(r"pub struct Calls\s*\{(.*?)\n\}", source, re.S)
    need(match is not None, "missing CT125 Calls definition")
    body = match.group(1)
    fields = re.findall(r"pub\s+([a-z_0-9]+)\s*:\s*u64\s*,", body)
    need(len(fields) == 21 and len(fields) == len(set(fields)),
         "expected 21 distinct u64 native counter declarations")
    return set(fields)


def u32_vector(value):
    return (type(value) is list and len(value) == 19 and
            all(type(v) is int and 0 <= v <= 0xffffffff for v in value))


def check_fixture(f, names):
    need(type(f) is dict and set(f) == {"all48", "scope"},
         "frozen root JSON schema")
    rows = f["all48"]
    need(type(rows) is list and len(rows) == 48, "exact 48 frozen packets")
    seen = set()
    total = 0
    for i, row in enumerate(rows):
        need(type(row) is dict, "row object " + str(i))
        need(u32_vector(row.get("input")) and u32_vector(row.get("whole_outputs_equal")),
             "typed 19-word public input/output " + str(i))
        a, b, sector, label = (row.get(k) for k in
                               ("from", "to", "sector", "scalar_OUTSIDE_runtime"))
        need(all(type(v) is int for v in (a, b, sector, label)),
             "typed source cohort " + str(i))
        need((a, b) in ((0, 2), (2, 0)) and sector in range(4) and
             label in (0, 1, 2, 17, 12345, 2771710), "cohort label")
        need((a, b, sector, label) not in seen, "duplicate cohort")
        seen.add((a, b, sector, label))
        for route in ROUTES:
            obj = row.get(route)
            need(type(obj) is dict and set(obj) == names,
                 "full 21-counter schema for " + route + " row " + str(i))
            need(all(type(v) is int and v >= 0 for v in obj.values()),
                 "native u64 counter not a nonnegative integer")
            total += 1
    need(total == 144, "exact 144 full counter objects")
    need(sum(1 for a, b, s, k in seen if k == 0) == 8, "eight identity cases")
    return total


def controls(f, source, names):
    variants = []
    r = copy.deepcopy(f)
    del r["all48"][0][ROUTES[0]]["degree169_elliptic_evaluation"]
    variants.append(r)
    r = copy.deepcopy(f)
    r["all48"][0][ROUTES[1]]["invented_count"] = 0
    variants.append(r)
    r = copy.deepcopy(f)
    r["all48"][0][ROUTES[2]]["transported_norm_doubling"] = True
    variants.append(r)
    r = copy.deepcopy(f)
    r["all48"][0]["whole_outputs_equal"][0] = False
    variants.append(r)
    r = copy.deepcopy(f)
    r["all48"][0]["scalar_OUTSIDE_runtime"] = 1.0
    variants.append(r)
    r = copy.deepcopy(f)
    r["all48"][0]["input"][0] = 2**32
    variants.append(r)
    r = copy.deepcopy(f)
    r["all48"][1] = r["all48"][0]
    variants.append(r)
    for mutated in variants:
        try:
            check_fixture(mutated, names)
        except ValueError:
            continue
        raise ValueError("accepted mutated actual 48-row evidence")
    altered = source.replace("pub degree13_elliptic_evaluation: u64,",
                             "pub degree131_elliptic_evaluation: u64,")
    need(altered != source, "CT125 mutation did not apply")
    try:
        check_fixture(f, rust_fields(altered))
    except ValueError:
        pass
    else:
        raise ValueError("accepted mutated real CT125 Calls layout")
    return len(variants) + 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    src_raw, fixture_raw = SOURCE.read_bytes(), FIXTURE.read_bytes()
    need(git_blob(src_raw) == SRC_BLOB, "changed CT125 actual Rust evaluator")
    need(git_blob(fixture_raw) == FIX_BLOB, "changed original frozen 48-row data")
    source = src_raw.decode("utf-8")
    names = rust_fields(source)
    fixture = strict_json(fixture_raw)
    total = check_fixture(fixture, names)
    negatives = controls(fixture, source, names) if args.self_test else 0
    print(json.dumps({
        "schema": "ct172-static-native-binding/v1",
        "standing": "[pcc:unverified]",
        "ct125_calls_git_blob": SRC_BLOB,
        "fixture_git_blob": FIX_BLOB,
        "native_u64_counter_fields": len(names),
        "frozen_real_packets": 48,
        "exact_full_counter_objects": total,
        "mutations_rejected": negatives,
        "scope": "source-only CT125 struct/real-fixture parity; no native run or timing"
    }, sort_keys=True))


if __name__ == "__main__":
    main()
