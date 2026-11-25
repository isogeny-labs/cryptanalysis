#!/usr/bin/env python3
"""Summarize the round-2 local profile and exactness records (diagnostic only).

LOCAL DIAGNOSTIC, NOT EVIDENCE. The raw records in `raw2/` come from the
shared cloud-agent VM (4 vCPU Intel Xeon @ 2.10 GHz under a hypervisor, one
process pinned with `taskset -c 2`, transparent huge pages `madvise`, where
the GitHub runner of the parent's run had `always`; toolchain 1.97 rather
than the workflow's 1.99). They rank candidates, size the design and check
exactness; no speedup is claimed from them.

Inputs:

* `raw2/profile_M38.json` (+ `.stderr.txt`): one process of the profiling
  build (`profile2_patch.py` on a scratch COPY of the row's producer, never
  committed as a producer), `KIC_INDEX_PROFILE2=1`, M38 closure header: the
  producer's index build, its components alone, and the candidates, each
  asserted equal to the producer's output.
* `raw2/bench_M38.json` (+ `.stderr.txt`): the same build,
  `KIC_INDEX_PROFILE2=bench`, 5 rounds in rotated order: the insert
  pipelines on one pre-faulted, re-zeroed table (so first-touch faults are
  out of the comparison), the state loops and the self-tests.
* `raw2/exactness_{K600,M38,M10}.json`: `exactness2_patch.py` on a scratch
  copy of the round-2 producer: its states and slot words against the
  parent's loops (verbatim), and its linear keys against lift_scan on every
  stored root of the base.
* `raw2/arm/*.txt`: `arm.py` processes (the full per-process gate set) of
  both binaries: Q0 on cPIC, cM10IC, cM38IC and cM38ICX; rank processes
  kM38IB and kM38IC with seed 1501 on point s000 of this panel; and
  alternating cold processes cM38IB / cM38IC on s000 (the modelled
  index-build factor).
"""

import base64
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw2"
PROFILE_OUT = HERE.parent / "inputs" / "local_profile.json"
EXACT_OUT = HERE.parent / "inputs" / "local_exactness.json"


def arm_record(path):
    line = next(l for l in path.read_text().splitlines() if l.startswith("raw_b64="))
    raw = json.loads(base64.b64decode(line[len("raw_b64="):]))
    summary = next((r for r in raw["records"] if r.get("kind") == "compact_orbit_dlp_summary"), {})
    return raw, summary


def main():
    prof = json.loads((RAW / "profile_M38.json").read_text())
    bench = json.loads((RAW / "bench_M38.json").read_text())["bench"]
    med = {k: statistics.median(v) for k, v in bench.items()}
    canon = {k: statistics.median(v["ms"]) for k, v in prof["canon"].items()}
    canon_equal = all(v["equal"] for v in prof["canon"].values())
    c6 = prof["c6_bucketed"]
    arms = {}
    for path in sorted((RAW / "arm").glob("*.txt")):
        raw, summary = arm_record(path)
        arms[path.stem] = {"issues": raw["issues"], "fields": raw["fields"],
                           "rank_attempt_probes": summary.get("rank_attempt_probes")}
    pairs = sorted(k for k in arms if k.startswith("A-cM38IB-s000-"))
    a_index = [arms[k]["fields"]["index_ms"] for k in pairs]
    b_index = [arms[k.replace("A-cM38IB", "B-cM38IC")]["fields"]["index_ms"] for k in pairs]
    a_cold = [arms[k]["fields"]["cold_ms"] for k in pairs]
    b_cold = [arms[k.replace("A-cM38IB", "B-cM38IC")]["fields"]["cold_ms"] for k in pairs]
    factor = sum(b_index) / sum(a_index)
    profile = {
        "schema": 1,
        "label": "LOCAL DIAGNOSTIC (shared cloud-agent VM): ranks candidates and sizes the design; not evidence",
        "host": "4 vCPU Intel Xeon @ 2.10 GHz, hypervisor guest, taskset -c 2, THP madvise, rustc 1.97",
        "base": "M38 closure header: 608 orbits, %d stored states, %d roots, %d entries, %d slots of 16 B" % (
            prof["stored_states"], 2 * prof["stored_states"], prof["table_entries"], prof["table_slots"]),
        "breakdown_median_ms": {
            "index_build_total_ms": prof["producer_index_build"]["ms"],
            "index_build_minor_faults": prof["producer_index_build"]["minflt"],
            "state_loop_ms": prof["producer_state_loop"]["ms"],
            "state_split_ms (instrumented copy, per-row timers)": prof["state_split"],
            "canonicalization_lift_scan_alone_ms": canon["lift_scan"],
            "insert_alone_prefetch32_ms (incl. faults)": prof["insert_only_pf32"]["ms"],
            "insert_alone_no_prefetch_ms (incl. faults)": prof["insert_only_pf0"]["ms"],
            "first_touch_faults_alone_ms (1 GiB, read then write per page)": prof["touch_read_write_per_page"]["ms"],
            "producer_insert_pipeline_ms (incl. faults)": prof["pipeline32_lift_scan"]["ms"],
            "bench_insert_pipeline_prefaulted_ms (producer, median of 5)": med["pipe32_lift"],
            "bench_state_loop_ms (producer, median of 5)": med["states_producer"],
            "bench_scan_selftest_ms (producer, 2 keys, median of 5)": med["selftest_producer"],
        },
        "canonicalizers_ms (all 30.7 M roots, median of 3; equal to lift_scan on every root: %s)" % canon_equal: canon,
        "candidates": {
            "C7_linear_canon_lanes8": {
                "bench_pipeline_ms": med["pipe32_linear_lanes8"], "producer_bench_pipeline_ms": med["pipe32_lift"],
                "modelled_saving_ms": med["pipe32_lift"] - med["pipe32_linear_lanes8"], "status": "implemented",
                "also": {"pipe32_linear": med["pipe32_linear"], "block32_linear": med["block32_linear"],
                         "block64_linear": med["block64_linear"], "block32_lift": med["block32_lift"]}},
            "C9_sum_inverse_states": {
                "bench_state_loop_ms": med["states_c9"], "producer_bench_state_loop_ms": med["states_producer"],
                "modelled_saving_ms": med["states_producer"] - med["states_c9"], "status": "implemented",
                "profile_runs_ms": {"producer": [prof["states_producer_rep0"]["ms"], prof["states_producer_rep1"]["ms"]],
                                    "c9": [prof["states_c9_rep0"]["ms"], prof["states_c9_rep1"]["ms"]]}},
            "C8_pclmul_codegen": {
                "profile_runs_ms": {"parent_loop_tf": [prof["states_parent_tf_rep0"]["ms"], prof["states_parent_tf_rep1"]["ms"]],
                                    "c9_tf": [prof["states_c9_tf_rep0"]["ms"], prof["states_c9_tf_rep1"]["ms"]]},
                "status": "rejected (no saving over the same loops without it)"},
            "C6_bucketed_insert": {
                "per_bucket_count": c6, "producer_insert_alone_prefetch32_ms": prof["insert_only_pf32"]["ms"],
                "status": "rejected (exact with the spill carry, but partition plus bucket inserts cost more than "
                          "the prefetched insert)"},
            "S3_branchfree_selftest": {
                "bench_ms": med["selftest_branchfree"], "producer_bench_ms": med["selftest_producer"],
                "status": "rejected (no saving beyond noise)"},
        },
        "local_cold_pairs_s000": {"A_cM38IB_index_ms": a_index, "B_cM38IC_index_ms": b_index,
                                  "A_cold_ms": a_cold, "B_cold_ms": b_cold,
                                  "order": "A then B, three times, one fresh pinned process each"},
        "modelled": {"index_build_factor": factor, "scan_selftest_factor": 1.0,
                     "source": "round-2 index build over the row's in the alternating local cold pairs (s000)"},
        "bench_rounds_ms": bench,
    }
    PROFILE_OUT.write_text(json.dumps(profile, indent=1, sort_keys=True) + "\n")
    bases = {name: json.loads((RAW / ("exactness_%s.json" % name)).read_text()) for name in ("K600", "M38", "M10")}
    exact = {
        "schema": 1,
        "label": "LOCAL CORRECTNESS CHECK (cloud-agent VM); the run re-checks every gate per process",
        "whole_base": bases,
        "whole_base_pass": all(b["states_equal_parent"] and b["slots_equal_parent"] and
                               b["linear_vs_lift_scan_key_mismatches"] == 0 and
                               b["linear_vs_lift_scan_shift_mismatches"] == 0 for b in bases.values()),
        "arm_processes": {k: {"issues": v["issues"], "relation": v["fields"].get("relation"),
                              "probes": v["fields"].get("ops"), "scalar": str(v["fields"].get("recovered_scalar")),
                              "layout_digest": v["fields"].get("layout_digest"),
                              "index_build_pipeline": v["fields"].get("index_build_pipeline"),
                              "index_plant_checked_inputs": v["fields"].get("index_plant_checked_inputs"),
                              "logs_equal_archived": v["fields"].get("logs_equal_archived"),
                              "rank_relations_blake3": v["fields"].get("rank_relations_blake3"),
                              "rank_root_calls_total": v["fields"].get("rank_root_calls_total"),
                              "rank_attempt_probes": v["rank_attempt_probes"]} for k, v in arms.items()},
        "rank_seed_1501_identical_across_binaries": (
            arms["A-kM38IB-1501"]["fields"]["rank_relations_blake3"] == arms["B-kM38IC-1501"]["fields"]["rank_relations_blake3"]
            and arms["A-kM38IB-1501"]["rank_attempt_probes"] == arms["B-kM38IC-1501"]["rank_attempt_probes"]
            and arms["A-kM38IB-1501"]["fields"]["rank_root_calls_total"] == arms["B-kM38IC-1501"]["fields"]["rank_root_calls_total"]),
        "every_arm_process_without_issue": all(not v["issues"] for v in arms.values()),
    }
    EXACT_OUT.write_text(json.dumps(exact, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"modelled_index_build_factor": factor, "whole_base_pass": exact["whole_base_pass"],
                      "rank_identical": exact["rank_seed_1501_identical_across_binaries"],
                      "arms_ok": exact["every_arm_process_without_issue"],
                      "c7_saving": profile["candidates"]["C7_linear_canon_lanes8"]["modelled_saving_ms"],
                      "c9_saving": profile["candidates"]["C9_sum_inverse_states"]["modelled_saving_ms"]}))


if __name__ == "__main__":
    main()
