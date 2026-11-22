#!/usr/bin/env python3
"""CT311: directional, sector-stratified scoped norm-reuse timer frontier.

Production requires CT304 complete paired capture. Output NEVER states a full
cold ECDLP cost or independent timing/PCC verification.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import ct248_scoped_sample_audit as ct248
import ct300_authentic_fixture_guard as ct300
import ct304_execution_receipt_gate as ct304


def refuse(message):
    raise ValueError("CT311: " + message)


def exact_median(values):
    if not values:
        refuse("cannot take an empty median")
    v = sorted(values)
    n = len(v)
    numerator = 2 * v[n // 2] if n % 2 else v[n // 2 - 1] + v[n // 2]
    return {"numerator": numerator, "denominator": 2}


def summarize(rows):
    ds = [r["direct_minus_retained_ns"] for r in rows]
    ms = [r["map_delta_ns"] for r in rows]
    dn = [r["doubling_delta_ns"] for r in rows]
    return {
        "n": len(rows),
        "positive": sum(x > 0 for x in ds),
        "zero": sum(x == 0 for x in ds),
        "negative": sum(x < 0 for x in ds),
        "paired_delta_median_ns": exact_median(ds),
        "map_delta_median_ns": exact_median(ms),
        "doubling_delta_median_ns": exact_median(dn),
        "all_nonzero_clocks": all(r["total_nonzero"] for r in rows),
    }


def scoped_price(raw, fixture_bytes):
    # Upstream captures must also pass the whole original/reuse CT304 gate.
    ct248.audit(raw)
    ct300.bind_transcript_to_frozen(raw, fixture_bytes)
    samples, vectors, lifetime = ct248.decode(raw)
    out = []
    for i, entry in enumerate(vectors["all48"]):
        a, lit, b = samples[3 * i:3 * i + 3]
        if not (a["sequence"], lit["sequence"], b["sequence"]) == (3*i, 3*i+1, 3*i+2):
            refuse("selected triplet ordering changed")
        fr, to = entry["from"], entry["to"]
        direction = f"{fr}_to_{to}"
        direct_map = sum(a["elapsed_ns"][4:6])
        retained_map = sum(b["elapsed_ns"][:4])
        direct_d = a["elapsed_ns"][6]
        retained_d = b["elapsed_ns"][6]
        map_delta = direct_map - retained_map
        doubling_delta = direct_d - retained_d
        out.append({
            "index": i,
            "direction": direction,
            "sector": entry["sector"],
            "scalar_label_outside_runtime": entry["scalar_OUTSIDE_runtime"],
            "direct_map_ns": direct_map,
            "retained_two_C13_map_ns": retained_map,
            "direct_D_ns": direct_d,
            "retained_D_ns": retained_d,
            "map_delta_ns": map_delta,
            "doubling_delta_ns": doubling_delta,
            "direct_minus_retained_ns": map_delta + doubling_delta,
            "literal_control_ns": sum(lit["elapsed_ns"]),
            "total_nonzero": (direct_map + retained_map + direct_d + retained_d) > 0,
        })
    if len(out) != 48:
        refuse("expected 48 paired selected rows")
    directions = {}
    by_direction_sector = {}
    for d in ("0_to_2", "2_to_0"):
        group = [r for r in out if r["direction"] == d]
        if len(group) != 24:
            refuse("direction split differs from 24 + 24")
        directions[d] = summarize(group)
        sectors = {}
        for s in range(4):
            g = [r for r in group if r["sector"] == s]
            if len(g) != 6:
                refuse("sector split differs from six")
            sectors[str(s)] = summarize(g)
        by_direction_sector[d] = sectors
    return {
        "schema": "ct311-directional-scoped-primitive-frontier/v1",
        "optimized_stdout_sha256": hashlib.sha256(raw.encode("utf8")).hexdigest(),
        "original_native_model_executions_independently_verified": False,
        "physical_timing_independently_reproduced": False,
        "primitive_timing_scope": "CT248 reset-calls-to-calls eval_and_padd_only; uncalibrated",
        "direct_against": "strongest_retained_lift_chain",
        "rows": out,
        "directions": directions,
        "direction_sectors": by_direction_sector,
        "whole_cold_single_target_ecdlp_cost": None,
        "native_execution_independently_verified": False,
        "pcc": "unverified",
    }


def self_test(fixture_path):
    # Authentic source VALUES but every elapsed ns below is fabricated.
    raw_fixture = fixture_path.read_bytes()
    doc = ct300.load_frozen(raw_fixture)
    source = ct300.build_mock_transcript(doc)
    samples, vectors, life = ct248.decode(source)

    def fabricate(price, sector_override=None):
        entries = copy.deepcopy(samples)
        for i, e in enumerate(entries):
            q = list(price)
            if (sector_override is not None and (i // 3) >= 24
                    and vectors["all48"][i // 3]["sector"] == sector_override):
                q[5] = 40
            e["elapsed_ns"] = [q[j] * e["calls"][j] for j in range(7)]
        l = copy.deepcopy(life)
        l["elapsed_ns"] = [sum(e["elapsed_ns"][j] for e in entries)
                           for j in range(7)]
        l["calls"] = [sum(e["calls"][j] for e in entries)
                      for j in range(7)]
        return ct248.encode(entries, vectors, l)

    # Both directions: direct 120+10, retained 2*40+10 => +40 ns.
    positive = scoped_price(fabricate([40,40,40,40,120,120,10]), raw_fixture)
    if not all(positive["directions"][d]["positive"] == 24 for d in ("0_to_2","2_to_0")):
        raise AssertionError("synthetic positive directional frontier was missed")
    # Both directions: direct 60+10, retained 80+10 => -20 ns.
    negative = scoped_price(fabricate([40,40,40,40,60,60,10]), raw_fixture)
    if not all(negative["directions"][d]["negative"] == 24 for d in ("0_to_2","2_to_0")):
        raise AssertionError("synthetic negative directional frontier was missed")
    # Reverse only sector 2 for direction 2->0: direct 40, retained 80.
    reversal = scoped_price(fabricate([40,40,40,40,120,120,10],2), raw_fixture)
    g = reversal["direction_sectors"]["2_to_0"]
    if not (g["2"]["negative"] == 6 and
            all(g[str(s)]["positive"] == 6 for s in (0,1,3))):
        raise AssertionError("synthetic sector-specific reversal was obscured")
    for r in reversal["rows"]:
        if (r["direct_minus_retained_ns"] !=
                r["map_delta_ns"] + r["doubling_delta_ns"]):
            raise AssertionError("arithmetic accounting drift")
    if reversal["whole_cold_single_target_ecdlp_cost"] is not None:
        raise AssertionError("synthetic primitive clock was promoted to a full solve")
    return {
        "schema":"ct311-source-only-synthetic-test/v1",
        "frozen_selected_source_rows":48,
        "synthetic_primitive_timing_rows":144,
        "positive_directional_controls":2,
        "negative_directional_controls":2,
        "negative_sector_reversal_controls":1,
        "original_native_model_executions":0,
        "physical_primitive_timings":0,
        "pcc":"unverified",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--capture-dir", type=Path)
    parser.add_argument("--self-test", action="store_true")
    a = parser.parse_args()
    if a.self_test:
        if a.capture_dir is not None:
            parser.error("synthetic self-test cannot consume real capture")
        print(json.dumps(self_test(a.fixture), sort_keys=True))
        return
    if a.capture_dir is None:
        parser.error("production requires --capture-dir with two complete captured logs/receipts")
    c = a.capture_dir
    admission = ct304.verify_pair(
        c/"original.stdout", c/"reuse.stdout", c/"original.stderr",
        c/"reuse.stderr", c/"original.bin", c/"reuse.bin",
        c/"original.receipt.json", c/"reuse.receipt.json", a.fixture)
    if admission["full_695_and_144_population_consistent"] is not True:
        refuse("incomplete or missing full-population capture")
    raw = (c/"reuse.stdout").read_text(encoding="utf8")
    result = scoped_price(raw, a.fixture.read_bytes())
    result["original_stdout_sha256"] = hashlib.sha256(
        (c/"original.stdout").read_bytes()).hexdigest()
    result["full_695_dual_native_transcript_admitted"] = True
    result["source_of_scoped_timer_values"] = "captured optimized stdout; uncalibrated"
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
