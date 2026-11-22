#!/usr/bin/env python3
"""Write inputs/local_profile.json and inputs/local_exactness.json from profile/raw/ (LOCAL DIAGNOSTICS).

* `prof_<side>_<mode>_<i>.*`: the instrumented scratch copies of the row's
  producer (parent) and the rank-finder producer (derived) from
  `profile_patch.py`, run by `run_profile.sh` on M38, rank seed 1501, two
  rounds, modes off (timers only) and canon (plus the canonicalization
  alone on every state's real partner words).
* `exactness_<base>*.json`: `exactness_rank.py`, both unpatched binaries,
  alternating, per seed.

The modelled rank-stage factor is the ratio of sums of the derived over the
parent rank stage in the alternating M38 exactness processes with
KIC_RANK_SOLVE=frame (exactness_M38.json); a cloud-agent-VM figure that
only sizes the design.
"""

import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
INPUTS = HERE.parent / "inputs"


def prof(side, mode, i):
    stderr = (RAW / ("prof_%s_%s_%d.stderr.txt" % (side, mode, i))).read_text()
    line = next(l for l in stderr.splitlines() if l.startswith("rankprof="))
    record = json.loads(line[len("rankprof="):])
    summary = json.loads((RAW / ("prof_%s_%s_%d.stdout.jsonl" % (side, mode, i))).read_text().splitlines()[-1])
    record["rank_stage_ms"] = summary["timing_ms"]["rank_stage"]
    record["rank_probes_total"] = summary["rank_probes_total"]
    return record


def main():
    rounds = (1, 2)
    profile = {}
    for side in ("parent", "derived"):
        off = [prof(side, "off", i) for i in rounds]
        canon = [prof(side, "canon", i) for i in rounds]
        rank = statistics.mean(r["rank_stage_ms"] for r in off)
        setup = statistics.mean(r["setup_ns"] for r in off) / 1e6
        keys = statistics.mean(r["keys_ns"] for r in off) / 1e6
        profile[side] = {
            "rank_stage_ms": rank, "frame_setup_ms": setup, "key_derivation_ms": keys,
            "probe_loop_and_rest_ms": rank - setup - keys,
            "keys": off[0]["keys"], "states": off[0]["states"], "probes": off[0]["rank_probes_total"],
            "lift_scan_alone_ms": statistics.mean(r["lift_alone_ns"] for r in canon) / 1e6,
            "linear_lanes8_alone_ms": statistics.mean(r["linear_alone_ns"] for r in canon) / 1e6,
            "rounds": {"off": off, "canon": canon}}
    for side in profile.values():
        side["ns_per_key"] = {k: side[k] * 1e6 / side["keys"] for k in
                              ("key_derivation_ms", "lift_scan_alone_ms", "linear_lanes8_alone_ms")}
    exact = {}
    for path in sorted(RAW.glob("exactness_*.json")):
        exact[path.stem] = json.loads(path.read_text())
    m38 = exact["exactness_M38"]
    factor = sum(e["sides"]["derived"]["rank_stage_ms"] for e in m38) / \
        sum(e["sides"]["parent"]["rank_stage_ms"] for e in m38)
    per_base = {}
    for name, entries in exact.items():
        for e in entries:
            b = per_base.setdefault(e["base"] + ("_" + e["solve"] if e["solve"] != "frame" else ""),
                                    {"seeds": [], "identical": True, "parent_ms": 0.0, "derived_ms": 0.0})
            b["seeds"].append(e["seed"])
            b["identical"] &= e["identical"] and all(e["logs_equal_frozen"]) and e["layout_digest_frozen"]
            b["parent_ms"] += e["sides"]["parent"]["rank_stage_ms"]
            b["derived_ms"] += e["sides"]["derived"]["rank_stage_ms"]
    for b in per_base.values():
        b["derived_over_parent_rank_stage"] = b["derived_ms"] / b["parent_ms"]
    out = {
        "schema": 1,
        "label": "LOCAL DIAGNOSTIC: shared cloud-agent VM, one pinned CPU, rustc 1.97; ranks and sizes only",
        "profile_M38_seed1501": {k: {kk: vv for kk, vv in v.items() if kk != "rounds"} for k, v in profile.items()},
        "profile_rounds": {k: v["rounds"] for k, v in profile.items()},
        "rank_stage_per_base": per_base,
        "modelled": {"rank_stage_factor": factor,
                     "source": "exactness_M38.json: 4 alternating seed pairs (1501, 301, 7001, 7002), KIC_RANK_SOLVE=frame"},
    }
    (INPUTS / "local_profile.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    exactness = {
        "schema": 1,
        "label": "LOCAL CORRECTNESS: exactness_rank.py, parent ic_online_indexbuild2_r770 vs ic_online_rankfinder_r770",
        "checked_per_seed": ["rank_relations_blake3", "rank_attempt_probes", "rank_root_calls_total",
                             "rank_probes_total", "rank_rows_without_gain", "rank_attempts", "rank_relations",
                             "rank_failures", "rank_padd_* counters", "rank_frame_builds",
                             "rank_skipped_symmetric_states", "index_digest (incl. layout digests)",
                             "root_table_entries", "stored_states", "regular_states",
                             "target relation, probes, scalar, filter passes",
                             "written factor-log table equal to the base's frozen table"],
        "all_identical": all(b["identical"] for b in per_base.values()),
        "per_base": {k: {"seeds": v["seeds"], "identical": v["identical"]} for k, v in per_base.items()},
        "runs": {name: [{k: e[k] for k in ("seed", "base", "solve", "identical", "logs_equal_frozen",
                                            "layout_digest_frozen", "order")} |
                        {"identity": e["sides"]["parent"]["identity"],
                         "derived_rank_probe_pipeline": e["sides"]["derived"]["rank_probe_pipeline"],
                         "plant_checked": {s: e["sides"][s]["rank_frame_plant_checked_inputs"]
                                           for s in ("parent", "derived")}}
                        for e in entries] for name, entries in exact.items()},
    }
    (INPUTS / "local_exactness.json").write_text(json.dumps(exactness, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"profile": out["profile_M38_seed1501"], "per_base": per_base, "modelled": out["modelled"],
                      "all_identical": exactness["all_identical"]}, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
