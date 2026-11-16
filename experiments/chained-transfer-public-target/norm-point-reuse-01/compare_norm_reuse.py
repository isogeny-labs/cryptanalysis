#!/usr/bin/env python3
"""Compare complete ordered native logs, permitting only preregistered reuse counts.

Requires TWO actual independent native test logs; neither synthetic tests nor
48 selected vectors alone certify the full 695-record parity or an ECDLP win.
"""
import argparse
import copy
import json
import math
import re
from collections import Counter
from pathlib import Path

TAG = re.compile(r"(N4_FIXED_CHAIN_[A-Z0-9_]+) (\{.*\})$")
ROUTES = {
    "direct_composite": ("degree169_elliptic_evaluation", 2, 1, 1),
    "literal_sequential_Jacobian_maps": ("degree13_elliptic_evaluation", 4, 2, 2),
    "strongest_retained_lift_chain": ("degree13_elliptic_evaluation", 4, 2, 1),
}

def require(ok, msg):
    if not ok:
        raise ValueError(msg)

def exact_json_equal(a, b):
    """Preserve types: Python equality conflates bool, int and float."""
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return a.keys() == b.keys() and all(
            exact_json_equal(a[key], b[key]) for key in a
        )
    if type(a) is list:
        return len(a) == len(b) and all(
            exact_json_equal(x, y) for x, y in zip(a, b)
        )
    if type(a) is float:
        return math.isfinite(a) and math.isfinite(b) and a == b
    return a == b


def reject_non_json_constant(value):
    raise ValueError(f"non-standard JSON numeric constant: {value}")


def no_duplicate_keys(items):
    result = {}
    for key, val in items:
        require(key not in result, f"duplicate JSON key {key}")
        result[key] = val
    return result

def events(path):
    out = []
    for line in path.read_text("utf-8").splitlines():
        if "N4_FIXED_CHAIN_" not in line:
            continue
        match = TAG.search(line.strip())
        require(match is not None, "malformed tagged native record")
        out.append((match[1], json.loads(
            match[2], object_pairs_hook=no_duplicate_keys,
            parse_constant=reject_non_json_constant)))
    return out

def check(original, optimized, expected_count=695):
    require(len(original) == len(optimized) == expected_count,
            f"whole record count mismatch; must be {expected_count}")
    tags = Counter(tag for tag, _ in original)
    require(tags["N4_FIXED_CHAIN_SELECTED_CALL_VECTORS"] == 1,
            "one whole selected-call vector event required")
    require(tags["N4_FIXED_CHAIN_EXCEPTIONAL_CASE"] == 672,
            "all 672 individual exceptional descriptors required")
    require(Counter(tag for tag, _ in optimized) == tags, "whole tag multiplicities differ")
    changed = 0
    for i, ((tag, a), (other_tag, b)) in enumerate(zip(original, optimized)):
        require(tag == other_tag, f"whole event order differs at {i}")
        if tag != "N4_FIXED_CHAIN_SELECTED_CALL_VECTORS":
            require(exact_json_equal(a, b), f"unexpected changed whole event at {i}/{tag}")
            continue
        require(type(a) is dict and type(b) is dict and set(a) == set(b),
                "selected event changed schema")
        require(set(a) == {"all48", "scope"} and exact_json_equal(a["scope"], b["scope"]),
                "selected event scope changed")
        oldrows, newrows = a["all48"], b["all48"]
        require(type(oldrows) is list and type(newrows) is list and
                len(oldrows) == len(newrows) == 48, "all48 required")
        directions, sectors = Counter(), Counter()
        for j, (old, new) in enumerate(zip(oldrows, newrows)):
            require(type(old) is dict and type(new) is dict and set(old) == set(new),
                    f"row {j} schema")
            require(all(exact_json_equal(old[k], new[k]) for k in old if k not in ROUTES),
                    f"row {j} changed public input/output")
            directions[(old["from"], old["to"])] += 1
            sectors[old["sector"]] += 1
            for route, (field, before, after, doubles) in ROUTES.items():
                o, n = old[route], new[route]
                require(type(o) is dict and type(n) is dict, f"route {j}/{route} schema")
                require("norm_point_doubling" not in o, "baseline already optimized")
                require(set(n) == set(o) | {"norm_point_doubling"},
                        f"unexpected fields {j}/{route}")
                require(type(o[field]) is int and type(n[field]) is int and
                        o[field] == before and n[field] == after,
                        f"incorrect map-call reduction {j}/{route}")
                require(type(n["norm_point_doubling"]) is int and
                        n["norm_point_doubling"] == doubles,
                        f"wrong new doubling count {j}/{route}")
                require(all(exact_json_equal(o[k], n[k]) for k in o if k != field),
                        f"hidden counter change {j}/{route}")
                changed += 1
    require(directions == Counter({(0, 2): 24, (2, 0): 24}),
            "source direction imbalance")
    require(sectors == Counter({s: 12 for s in range(4)}),
            "all four cofactor sectors required")
    require(changed == 144, "all 48x3 route counts required")
    return {
        "whole_records": expected_count,
        "exceptional_records": 672,
        "selected_rows": 48,
        "selected_route_counters_checked": changed,
        "status": "[pcc:unverified]; original and optimized native execution required; no timed cost or ECDLP speedup",
    }

def self_test():
    orig = [("N4_FIXED_CHAIN_EXCEPTIONAL_CASE", {"index": i}) for i in range(672)]
    orig += [("N4_FIXED_CHAIN_OTHER", {"i": i}) for i in range(22)]
    rows = []
    for fr, to in ((0, 2), (2, 0)):
        for sector in range(4):
            for j in range(6):
                row = {"from": fr, "to": to, "sector": sector,
                       "input": [fr, to, sector, j]}
                for route, (field, before, after, doubles) in ROUTES.items():
                    row[route] = {field: before, "untouched": j}
                rows.append(row)
    orig.append(("N4_FIXED_CHAIN_SELECTED_CALL_VECTORS",
                 {"all48": rows, "scope": "immutable"}))
    opt = copy.deepcopy(orig)
    for row in opt[-1][1]["all48"]:
        for route, (field, before, after, doubles) in ROUTES.items():
            row[route][field] = after
            row[route]["norm_point_doubling"] = doubles
    require(check(orig, opt)["selected_route_counters_checked"] == 144,
            "positive control")
    variants = []
    bad = copy.deepcopy(opt); bad.pop(0); variants.append(bad)
    bad = copy.deepcopy(opt); bad[0][1]["index"] = 999; variants.append(bad)
    bad = copy.deepcopy(opt); bad[-1][1]["all48"][0]["input"] = [-1]; variants.append(bad)
    bad = copy.deepcopy(opt); bad[-1][1]["all48"][0]["direct_composite"]["norm_point_doubling"] = 0; variants.append(bad)
    bad = copy.deepcopy(opt); bad[-1][1]["all48"][0]["strongest_retained_lift_chain"]["untouched"] = 9; variants.append(bad)
    bad = copy.deepcopy(opt); bad[0], bad[1] = bad[1], bad[0]; variants.append(bad)
    # CT157: five substitutions the legacy Python object equality accepts.
    bad = copy.deepcopy(opt); bad[0][1]["index"] = False; variants.append(bad)
    bad = copy.deepcopy(opt); bad[-1][1]["all48"][0]["input"][0] = False; variants.append(bad)
    bad = copy.deepcopy(opt)
    bad[-1][1]["all48"][0]["direct_composite"]["degree169_elliptic_evaluation"] = True
    variants.append(bad)
    bad = copy.deepcopy(opt)
    bad[-1][1]["all48"][0]["direct_composite"]["degree169_elliptic_evaluation"] = 1.0
    variants.append(bad)
    bad = copy.deepcopy(opt)
    bad[-1][1]["all48"][0]["direct_composite"]["untouched"] = False
    variants.append(bad)
    bad_orig = copy.deepcopy(orig)
    bad_orig[-1][1]["all48"][0]["direct_composite"]["degree169_elliptic_evaluation"] = 2.0
    try:
        check(bad_orig, opt)
    except ValueError:
        pass
    else:
        raise AssertionError("original-side integer-to-float counter accepted")
    for token in ("NaN", "Infinity", "-Infinity"):
        try:
            json.loads('{"value":' + token + '}', parse_constant=reject_non_json_constant)
        except ValueError:
            pass
        else:
            raise AssertionError(f"non-JSON numeric token accepted: {token}")
    for i, variant in enumerate(variants):
        try:
            check(orig, variant)
        except ValueError:
            continue
        raise AssertionError(f"negative control {i} wrongly accepted")
    return {"synthetic_695_record_control": "pass",
            "mutations_rejected": len(variants),
            "original_counter_type_mutations_rejected": 1,
            "non_json_numeric_tokens_rejected": 3}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--original", type=Path)
    ap.add_argument("--optimized", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return
    if not args.original or not args.optimized:
        ap.error("two complete native logs required, or --self-test")
    print(json.dumps(check(events(args.original), events(args.optimized)), sort_keys=True))

if __name__ == "__main__":
    main()
