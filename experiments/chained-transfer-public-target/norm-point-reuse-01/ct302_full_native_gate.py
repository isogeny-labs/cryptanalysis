#!/usr/bin/env python3
"""CT302: full 695-record dual-log and CT248/301 clock/source consistency gate.

Internal producer transcript consistency only. No independent native execution,
calibrated primitive timing, complete ECDLP solve, or signed PCC is certified.
"""
import argparse
import copy
import json
import tempfile
from pathlib import Path

import compare_norm_reuse as whole
import ct248_scoped_sample_audit as clocks
import ct300_authentic_fixture_guard as frozen

TRACE_MARKERS = (clocks.SAMPLE, clocks.VECTORS, clocks.LIFETIME)


def strict_trace_json(raw):
    """Disallow duplicate keys and nonstandard JSON numeric constants, even nested."""
    count = [0, 0, 0]
    for line in raw.splitlines():
        for j, marker in enumerate(TRACE_MARKERS):
            if line.startswith(marker):
                json.loads(line[len(marker):],
                           object_pairs_hook=whole.no_duplicate_keys,
                           parse_constant=whole.reject_non_json_constant)
                count[j] += 1
                break
    if count != [144, 1, 1]:
        raise ValueError(f"CT302 trace marker population differs: {count}")


def validate(original_log, optimized_log, fixture):
    """Require original and optimized whole native populations and CT301 binding."""
    whole_result = whole.check(whole.events(original_log), whole.events(optimized_log))
    raw = optimized_log.read_text(encoding="utf-8")
    strict_trace_json(raw)
    samples = clocks.audit(raw)
    frozen.bind_transcript_to_frozen(raw, fixture.read_bytes())
    if whole_result["whole_records"] != 695 or samples["scoped_samples"] != 144:
        raise ValueError("CT302 population/clock mismatch")
    return {
        "schema": "ct302-dual-population-source-audit-v1",
        "paired_original_and_reuse_full_records": 695,
        "matched_exceptional_records": 672,
        "matched_selected_source_vectors": 48,
        "reconciled_scoped_primitive_samples": 144,
        "immutable_selected_fixture_bound": True,
        "strict_tagged_json": True,
        "baseline_reuse_full_log_parity": True,
        "complete_single_target_ecdlp_cost": None,
        "native_execution_independently_verified": False,
        "physical_primitive_timing_independently_reproduced": False,
        "pcc": "unverified",
        "scope": "producer transcript consistency only; neither independent arithmetic nor a cold full solve"
    }


def synthetic_pair(fixture_bytes):
    """Authentic selected rows, SYNTHETIC 694 other rows and mock zero-ns clocks."""
    doc = frozen.load_frozen(fixture_bytes)
    optimized_trace = frozen.build_mock_transcript(doc)
    _, selected, _ = clocks.decode(optimized_trace)
    original_selected = copy.deepcopy(selected)
    for row in original_selected["all48"]:
        for route, (field, before, after, doubles) in whole.ROUTES.items():
            counter = row[route]
            if (counter[field], counter["norm_point_doubling"]) != (after, doubles):
                raise ValueError("CT302 synthetic original counts disagree with CT125 fixture")
            del counter["norm_point_doubling"]
            counter[field] = before
    prefix = "".join("N4_FIXED_CHAIN_EXCEPTIONAL_CASE " +
                     json.dumps({"index": i}) + "\n" for i in range(672))
    prefix += "".join("N4_FIXED_CHAIN_OTHER " +
                      json.dumps({"i": i}) + "\n" for i in range(22))
    original = prefix + clocks.VECTORS + json.dumps(original_selected, sort_keys=True) + "\n"
    candidate = prefix + optimized_trace
    return original, candidate


def self_test(fixture_path):
    b = fixture_path.read_bytes()
    original, candidate = synthetic_pair(b)
    with tempfile.TemporaryDirectory(prefix="ct302-source-only-") as td:
        root = Path(td)
        old, new, fixture = root / "original.log", root / "reuse.log", root / "fixture.json"
        def trial(o=original, n=candidate, f=b):
            old.write_text(o, encoding="utf-8")
            new.write_text(n, encoding="utf-8")
            fixture.write_bytes(f)
            return validate(old, new, fixture)
        good = trial()
        if (good["paired_original_and_reuse_full_records"],
                good["reconciled_scoped_primitive_samples"],
                good["native_execution_independently_verified"]) != (695, 144, False):
            raise AssertionError("CT302 source-only positive standing changed")

        def omit_first(t):
            return "\n".join(t.splitlines()[1:]) + "\n"

        def alter_exception(t):
            return t.replace('N4_FIXED_CHAIN_EXCEPTIONAL_CASE {"index": 0}',
                             'N4_FIXED_CHAIN_EXCEPTIONAL_CASE {"index": 999}', 1)

        def duplicate_primitive(t):
            anchor = '"sequence": 0'
            if anchor not in t:
                raise AssertionError("missing primitive sequence anchor")
            return t.replace(anchor, '"sequence": 0, "sequence": 0', 1)

        def non_json_nan(t):
            anchor = '"sequence": 0'
            if anchor not in t:
                raise AssertionError("missing primitive NaN anchor")
            return t.replace(anchor, '"sequence": NaN, "sequence": 0', 1)

        def remove_lifetime(t):
            return "\n".join(x for x in t.splitlines()
                             if not x.startswith(clocks.LIFETIME)) + "\n"

        def changed_selected_key(t):
            _, row, _ = clocks.decode(t)
            changed = copy.deepcopy(row)
            key = changed["all48"][0]["input"]
            key[3] = (key[3] + 1) % (2 ** 32)
            lines = [x for x in t.splitlines() if not x.startswith(clocks.VECTORS)]
            return "\n".join(lines) + "\n" + clocks.VECTORS + json.dumps(changed, sort_keys=True) + "\n"

        cases = [
            ("missing baseline event", lambda: trial(o=omit_first(original))),
            ("missing reuse event", lambda: trial(n=omit_first(candidate))),
            ("altered exceptional", lambda: trial(n=alter_exception(candidate))),
            ("selected-only mock", lambda: trial(n=frozen.build_mock_transcript(frozen.load_frozen(b)))),
            ("duplicate primitive key", lambda: trial(n=duplicate_primitive(candidate))),
            ("nonstandard JSON NaN", lambda: trial(n=non_json_nan(candidate))),
            ("omitted lifetime clock", lambda: trial(n=remove_lifetime(candidate))),
            ("altered public class key", lambda: trial(n=changed_selected_key(candidate))),
            ("altered immutable fixture", lambda: trial(f=b + b" ")),
            ("duplicated selected event", lambda: trial(
                n=candidate + clocks.VECTORS + json.dumps({"all48": [], "scope": "forged"}) + "\n")),
        ]
        for label, fn in cases:
            try:
                fn()
            except (ValueError, KeyError, TypeError):
                continue
            raise AssertionError("CT302 negative escaped: " + label)
    return {
        "schema": "ct302-source-only-selftest-v1",
        "authentic_selected_fixture_rows": 48,
        "synthetic_other_population_rows": 694,
        "synthetic_zero_ns_clock_samples": 144,
        "synthetic_positive": "pass",
        "synthetic_mutations_rejected": len(cases),
        "native_execution_performed": False,
        "complete_source_ecdlp_measured": False,
        "pcc": "unverified",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--original", type=Path)
    p.add_argument("--optimized", type=Path)
    p.add_argument("--fixture", type=Path, required=True)
    args = p.parse_args()
    if args.self_test:
        if args.original is not None or args.optimized is not None:
            p.error("--self-test never admits actual native files")
        print(json.dumps(self_test(args.fixture), sort_keys=True))
    else:
        if args.original is None or args.optimized is None:
            p.error("CT302 requires BOTH complete native logs")
        print(json.dumps(validate(args.original, args.optimized, args.fixture), sort_keys=True))


if __name__ == "__main__":
    main()
