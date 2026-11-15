#!/usr/bin/env python3
"""Summarise the local prototype (`inputs/local_prototype_rows.jsonl`) into `inputs/local_profile.json`.

The prototype (2026-11-07, a loaded shared 4-core cloud VM, one pinned core, 65 runs of the frozen
field-ops producer, `profile/prototype_driver.py`) ran four candidate headers against M38. D4 is its
header (d): K' = 4, `--norm 165`, 400 orbits. Everything here is a LOCAL DIAGNOSTIC: it sizes the
design (`power_check.py`) and ranks nothing. `modelled` carries the two setup factors the power check
uses: the index-build ratio D4 / M38 of the cold processes (means of three alternating rounds) and the
self-test ratio, which is set to the structural 0.25 (the Feistel domain steps down 2^26 -> 2^24) rather
than the measured cold ratio, because the prototype's cold M38 self-test (1540 ms) is the unexplained
high one (its rank-process median is 1000-1500 ms).
"""

import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROWS = HERE / "inputs" / "local_prototype_rows.jsonl"
OUT = HERE / "inputs" / "local_profile.json"
NAMES = {"M38": "M38", "d_K4_400": "D4 (header d)", "b_K4_612": "header b (K'=4, 612 orbits)",
         "a_K8_624": "header a (K'=8, 624 orbits)", "c_K8_448": "header c (K'=8, 448 orbits)"}


def main():
    rows = [json.loads(line) for line in ROWS.read_text().splitlines() if line.strip()]
    out = {"schema": 1, "label": "LOCAL DIAGNOSTIC: loaded shared 4-core VM, one pinned core; sizing only",
           "source": "inputs/local_prototype_rows.jsonl (65 runs), profile/prototype_driver.py", "arms": {}}
    for arm in NAMES:
        cold = [r for r in rows if r["arm"] == arm and r["kind"] == "cold"]
        rank = [r for r in rows if r["arm"] == arm and r["kind"] == "rank"]
        out["arms"][arm] = {
            "label": NAMES[arm], "cold_runs": len(cold), "rank_runs": len(rank),
            "orbits": rank[0]["orbits"], "columns": rank[0]["cols"], "table_entries": rank[0]["entries"],
            "cold_index_build_ms_mean": statistics.mean(r["index_build"] for r in cold),
            "cold_selftest_ms_mean": statistics.mean(r["selftest"] for r in cold),
            "cold_online_ms_mean": statistics.mean(r["online"] for r in cold),
            "rank_stage_ms_mean": statistics.mean(r["rank_stage"] for r in rank),
            "rank_process_total_ms_mean": statistics.mean(r["process_total"] for r in rank),
            "rank_process_total_ms_sd": statistics.stdev(r["process_total"] for r in rank),
            "all_solved_no_rank_failures": all(r["solved"] == 1 and r["failed"] == 0 and (r["rank_failures"] or 0) == 0
                                               and (r["rows_wo_gain"] or 0) == 0 for r in rows if r["arm"] == arm)}
    m, d = out["arms"]["M38"], out["arms"]["d_K4_400"]
    out["modelled"] = {
        "index_build_factor": d["cold_index_build_ms_mean"] / m["cold_index_build_ms_mean"],
        "selftest_factor": 0.25,
        "note": "measured cold self-test ratio %.3f is not used (see the docstring)" % (
            d["cold_selftest_ms_mean"] / m["cold_selftest_ms_mean"]),
        "local_e2e_ratio_M38_over_D4": m["rank_process_total_ms_mean"] / d["rank_process_total_ms_mean"]}
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps(out["modelled"], sort_keys=True))


if __name__ == "__main__":
    main()
