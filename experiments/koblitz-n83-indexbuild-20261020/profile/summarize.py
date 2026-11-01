#!/usr/bin/env python3
"""Summarize the local index-build profile into `inputs/local_profile.json` (diagnostic only).

LOCAL DIAGNOSTIC, NOT EVIDENCE. The raw records in `raw/` come from the
shared cloud-agent VM (4 vCPU Intel Xeon @ 2.10 GHz under KVM, other agents
running, one process pinned with `taskset -c 2`, toolchain 1.97 rather than
the workflow's 1.99). They rank candidates and size the design; no speedup is
claimed from them.

* `raw/profile_run{1,2,3}.json`: three processes of the profiling build
  (`profile_patch.py` applied to a scratch COPY of the row's producer; never
  committed as a producer) on the M38 closure header, `KIC_INDEX_PROFILE=all`.
  Each times the parent's index build in place (state loop, table insert with
  lift_scan canonicalization), then each component alone and each candidate
  variant, and asserts that every variant reproduces the parent's states and
  slot words. Minor faults come from `getrusage`.
* `raw/candidates.jsonl`: one fresh process per candidate stack
  (`KIC_INDEX_CANDIDATE=rows,lookahead,memory`), the full scan self-test and
  the eight-lane self-test in the same process; `4,32,plain` also rebuilt the
  parent's index and compared it (equal: true).
* `raw/cold_{parent,indexbuild}_s000.stdout.txt`: one `arm.py` cold process
  each of the row's producer and the derived producer on point s000 of the
  template's panel (not this experiment's panel), with the full gate set.
  The derived binary there was built from the derivation before a test-only
  edit (its source 5e4c9b21... differs from the frozen one only inside the
  `#[cfg(test)] mod indexbuild_tests` text), so its release code is the
  frozen producer's.

The summary is the median over the three profile runs of each component.
"""

import base64
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "inputs" / "local_profile.json"


def main():
    runs = [json.loads((HERE / "raw" / ("profile_run%d.json" % i)).read_text()) for i in (1, 2, 3)]
    keys = sorted(k for k, v in runs[0].items() if isinstance(v, dict))
    median = {k: statistics.median(r[k]["ms"] for r in runs) for k in keys}
    faults = {k: statistics.median(r[k]["minflt"] for r in runs) for k in keys}
    base_total = statistics.median(r["baseline_index_ms_total"] for r in runs)
    candidates = [json.loads(line) for line in (HERE / "raw" / "candidates.jsonl").read_text().splitlines() if line]
    states, insert = median["states_baseline"], median["table_insert_canon_baseline"]
    solve, prep, prep_inv = median["solve_only"], median["prepare_only"], median["prepare_invert_only"]
    selftest = median["selftest_full_key0"] + median["selftest_full_key1"]
    breakdown = {
        "index_build_total_ms": base_total,
        "state_loop_ms": states,
        "state_loop_parts_ms": {
            "s3_prepare": prep,
            "s3_field_inversion": prep_inv - prep,
            "s3_finish": solve - prep_inv,
            "to_normal_two_roots": median["to_normal_only"],
            "state_push_and_first_touch": median["states_push_only"],
        },
        "table_insert_loop_ms": insert,
        "table_insert_parts_ms": {
            "lift_scan_canonicalization": median["canon_only"],
            "insert_with_first_touch_faults": insert - median["canon_only"],
        },
        "table_allocation_ms": median["table_alloc_baseline"],
        "table_minor_faults": faults["table_insert_canon_baseline"],
        "table_bytes": runs[0]["table_slots"] * 16,
        "state_minor_faults": faults["states_baseline"],
        "scan_selftest_full_two_keys_ms": selftest,
        "scan_inverse_selftest_two_keys_ms": median["selftest_inverse_key0"] + median["selftest_inverse_key1"],
        "stored_states": runs[0]["stored_states"], "table_slots": runs[0]["table_slots"],
        "table_entries": runs[0]["table_entries"],
    }
    variants = {k: median[k] for k in keys if k.startswith(("states_batched", "insert_", "pipeline")) and
                not k.endswith(":alloc")}
    cand = {c["spec"]: {"candidate_index_ms": c["candidate_index_ms"], "selftest_full_ms": c["selftest_full_ms"],
                        "selftest_lanes_ms": c["selftest_lanes_ms"], "selftest_equal": c["selftest_equal"],
                        "layout_equal_to_parent": c["equal"], "parent_index_ms_same_process": c["baseline_index_ms"],
                        "minor_faults": c["candidate_minflt"]} for c in candidates}
    arms = {}
    for name in ("parent", "indexbuild"):
        lines = (HERE / "raw" / ("cold_%s_s000.stdout.txt" % name)).read_text().splitlines()
        raw = json.loads(base64.b64decode(next(l[8:] for l in lines if l.startswith("raw_b64="))))
        summary = next(r for r in raw["records"] if r.get("kind") == "compact_orbit_dlp_summary")
        arms[name] = {"issues": raw["issues"], "index_build_ms": summary["timing_ms"]["index_build"],
                      "scan_selftest_ms": summary["scan_order_selftest"]["ms"],
                      "cold_in_process_ms": summary["cold_in_process_ms"],
                      "index_build_pipeline": summary.get("index_build_pipeline"),
                      "layout": {k: summary["index_digest"][k] for k in ("stored_states_blake3", "table_slots_blake3")},
                      "probes": raw["fields"]["ops"], "relation": raw["fields"]["relation"]}
    out = {
        "schema": 1,
        "label": "LOCAL DIAGNOSTIC on the shared cloud-agent VM; ranks candidates and sizes the design, not evidence",
        "host": "cloud-agent VM, 4 vCPU Intel Xeon @ 2.10 GHz (KVM), kernel 6.18.44, THP madvise; taskset -c 2; "
                "rustc/cargo 1.97 (the workflow pins 1.99)",
        "base": "M38 closure header (608 orbits, 15,341,360 stored states, 30,366,551 root entries, 2^26 slots)",
        "profile_runs": 3,
        "breakdown_median_ms": breakdown,
        "variant_median_ms": variants,
        "candidate_processes": cand,
        "arm_cold_processes_s000": arms,
        "modelled": {
            "index_build_factor": arms["indexbuild"]["index_build_ms"] / arms["parent"]["index_build_ms"],
            "scan_selftest_factor": arms["indexbuild"]["scan_selftest_ms"] / arms["parent"]["scan_selftest_ms"],
            "basis": ("the derived producer's index build and self-test over the row producer's, one arm.py cold "
                      "process each on the same point, run back to back (raw/cold_*_s000.stdout.txt)"),
        },
    }
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps(out["breakdown_median_ms"], indent=1, sort_keys=True))
    print(json.dumps(out["modelled"], sort_keys=True))


if __name__ == "__main__":
    main()
